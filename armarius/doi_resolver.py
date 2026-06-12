"""DOI resolution and metadata enrichment via external APIs.

Queries Crossref, Semantic Scholar, and other services to enrich paper metadata.
"""

import time
from typing import Optional, Dict, Any
from dataclasses import dataclass
import urllib.parse
import urllib.request
import json


@dataclass
class ResolvedMetadata:
    """Metadata resolved from external APIs."""

    doi: Optional[str] = None
    title: Optional[str] = None
    authors: Optional[list[str]] = None
    year: Optional[int] = None
    venue: Optional[str] = None
    abstract: Optional[str] = None
    source: str = "none"  # crossref, semantic_scholar, none


class CrossrefResolver:
    """Resolve DOI and metadata via Crossref API.

    Crossref API documentation: https://www.crossref.org/documentation/retrieve-metadata/rest-api/
    Rate limit: 50 requests/second (no authentication required for polite usage)
    """

    API_URL = "https://api.crossref.org/works"
    POLITE_DELAY = 0.1  # 100ms delay between requests

    def __init__(self, mailto: Optional[str] = None):
        """Initialize Crossref resolver.

        Args:
            mailto: Email for polite API usage (gets better rate limits)
        """
        self.mailto = mailto
        self.last_request_time = 0

    def resolve_doi(self, doi: str) -> Optional[ResolvedMetadata]:
        """Resolve metadata for a given DOI.

        Args:
            doi: DOI string (e.g., "10.1000/xyz123")

        Returns:
            ResolvedMetadata object or None if not found
        """
        if not doi:
            return None

        # Rate limiting
        self._wait_for_rate_limit()

        try:
            # Build request URL
            url = f"{self.API_URL}/{urllib.parse.quote(doi)}"

            # Add polite headers
            headers = {"User-Agent": "Cardex/0.1"}
            if self.mailto:
                headers["User-Agent"] += f" (mailto:{self.mailto})"

            req = urllib.request.Request(url, headers=headers)

            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())

            # Parse response
            return self._parse_crossref_response(data)

        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"DOI not found in Crossref: {doi}")
            else:
                print(f"Crossref API error: {e.code} - {e.reason}")
            return None
        except Exception as e:
            print(f"Error resolving DOI via Crossref: {e}")
            return None

    def search_by_title(self, title: str) -> Optional[ResolvedMetadata]:
        """Search for paper by title and return best match.

        Args:
            title: Paper title

        Returns:
            ResolvedMetadata object or None if not found
        """
        if not title or len(title) < 10:
            return None

        self._wait_for_rate_limit()

        try:
            # Build query URL
            query = urllib.parse.quote(title)
            url = f"{self.API_URL}?query.title={query}&rows=1"

            headers = {"User-Agent": "Cardex/0.1"}
            if self.mailto:
                headers["User-Agent"] += f" (mailto:{self.mailto})"

            req = urllib.request.Request(url, headers=headers)

            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())

            # Get first result
            items = data.get("message", {}).get("items", [])
            if items:
                return self._parse_crossref_response({"message": items[0]})

            return None

        except Exception as e:
            print(f"Error searching Crossref by title: {e}")
            return None

    def _parse_crossref_response(self, data: Dict[str, Any]) -> Optional[ResolvedMetadata]:
        """Parse Crossref API response.

        Args:
            data: JSON response from Crossref API

        Returns:
            ResolvedMetadata object
        """
        try:
            message = data.get("message", {})

            metadata = ResolvedMetadata(source="crossref")

            # DOI
            metadata.doi = message.get("DOI")

            # Title (join array)
            titles = message.get("title", [])
            if titles:
                metadata.title = titles[0]

            # Authors
            authors = message.get("author", [])
            if authors:
                metadata.authors = [
                    f"{a.get('given', '')} {a.get('family', '')}".strip() for a in authors
                ]

            # Year
            date_parts = message.get("published-print", {}).get("date-parts", [[]])
            if not date_parts or not date_parts[0]:
                date_parts = message.get("published-online", {}).get("date-parts", [[]])
            if date_parts and date_parts[0]:
                metadata.year = date_parts[0][0]

            # Venue (journal or conference)
            venue = message.get("container-title", [])
            if venue:
                metadata.venue = venue[0]

            # Abstract (if available)
            metadata.abstract = message.get("abstract")

            return metadata

        except Exception as e:
            print(f"Error parsing Crossref response: {e}")
            return None

    def _wait_for_rate_limit(self):
        """Implement polite rate limiting."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.POLITE_DELAY:
            time.sleep(self.POLITE_DELAY - elapsed)
        self.last_request_time = time.time()


class SemanticScholarResolver:
    """Resolve metadata via Semantic Scholar API.

    Semantic Scholar API: https://www.semanticscholar.org/product/api
    Rate limit: 100 requests/5 minutes (no API key required)
    """

    API_URL = "https://api.semanticscholar.org/graph/v1/paper"
    POLITE_DELAY = 3.0  # 3 seconds between requests (conservative)

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Semantic Scholar resolver.

        Args:
            api_key: Optional API key for higher rate limits
        """
        self.api_key = api_key
        self.last_request_time = 0

    def resolve_doi(self, doi: str) -> Optional[ResolvedMetadata]:
        """Resolve metadata for a given DOI.

        Args:
            doi: DOI string

        Returns:
            ResolvedMetadata object or None
        """
        if not doi:
            return None

        self._wait_for_rate_limit()

        try:
            # Semantic Scholar accepts DOI as paper identifier
            url = f"{self.API_URL}/DOI:{urllib.parse.quote(doi)}"
            params = "?fields=title,authors,year,venue,abstract,doi"

            headers = {"User-Agent": "Cardex/0.1"}
            if self.api_key:
                headers["x-api-key"] = self.api_key

            req = urllib.request.Request(url + params, headers=headers)

            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())

            return self._parse_response(data)

        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"DOI not found in Semantic Scholar: {doi}")
            else:
                print(f"Semantic Scholar API error: {e.code}")
            return None
        except Exception as e:
            print(f"Error resolving via Semantic Scholar: {e}")
            return None

    def search_by_title(self, title: str) -> Optional[ResolvedMetadata]:
        """Search by title and return best match.

        Args:
            title: Paper title

        Returns:
            ResolvedMetadata object or None
        """
        if not title or len(title) < 10:
            return None

        self._wait_for_rate_limit()

        try:
            query = urllib.parse.quote(title)
            url = f"{self.API_URL}/search?query={query}&fields=title,authors,year,venue,abstract,doi&limit=1"

            headers = {"User-Agent": "Cardex/0.1"}
            if self.api_key:
                headers["x-api-key"] = self.api_key

            req = urllib.request.Request(url, headers=headers)

            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())

            # Get first result
            papers = data.get("data", [])
            if papers:
                return self._parse_response(papers[0])

            return None

        except Exception as e:
            print(f"Error searching Semantic Scholar: {e}")
            return None

    def _parse_response(self, data: Dict[str, Any]) -> Optional[ResolvedMetadata]:
        """Parse Semantic Scholar API response.

        Args:
            data: JSON response

        Returns:
            ResolvedMetadata object
        """
        try:
            metadata = ResolvedMetadata(source="semantic_scholar")

            metadata.doi = data.get("externalIds", {}).get("DOI") or data.get("doi")
            metadata.title = data.get("title")
            metadata.year = data.get("year")
            metadata.venue = data.get("venue")
            metadata.abstract = data.get("abstract")

            # Authors
            authors = data.get("authors", [])
            if authors:
                metadata.authors = [a.get("name", "") for a in authors]

            return metadata

        except Exception as e:
            print(f"Error parsing Semantic Scholar response: {e}")
            return None

    def _wait_for_rate_limit(self):
        """Implement conservative rate limiting."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.POLITE_DELAY:
            time.sleep(self.POLITE_DELAY - elapsed)
        self.last_request_time = time.time()


class DOIResolver:
    """Unified DOI resolver that tries multiple sources."""

    def __init__(self, mailto: Optional[str] = None, semantic_scholar_key: Optional[str] = None):
        """Initialize multi-source resolver.

        Args:
            mailto: Email for Crossref polite pool
            semantic_scholar_key: Optional Semantic Scholar API key
        """
        self.crossref = CrossrefResolver(mailto=mailto)
        self.semantic_scholar = SemanticScholarResolver(api_key=semantic_scholar_key)

    def resolve(
        self, doi: Optional[str] = None, title: Optional[str] = None
    ) -> Optional[ResolvedMetadata]:
        """Resolve metadata by DOI or title.

        Strategy:
        1. If DOI provided, try Crossref first (faster, more reliable)
        2. If not found or no DOI, try Semantic Scholar
        3. If title provided and no DOI, search by title

        Args:
            doi: DOI string (optional)
            title: Paper title (optional)

        Returns:
            ResolvedMetadata object or None
        """
        # Try DOI resolution first
        if doi:
            # Try Crossref
            metadata = self.crossref.resolve_doi(doi)
            if metadata and metadata.doi:
                return metadata

            # Fallback to Semantic Scholar
            metadata = self.semantic_scholar.resolve_doi(doi)
            if metadata and metadata.doi:
                return metadata

        # Try title search if DOI not found or not provided
        if title:
            # Try Crossref title search first
            metadata = self.crossref.search_by_title(title)
            if metadata and metadata.doi:
                return metadata

            # Fallback to Semantic Scholar
            metadata = self.semantic_scholar.search_by_title(title)
            if metadata and metadata.doi:
                return metadata

        return None
