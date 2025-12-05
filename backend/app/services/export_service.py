"""Export Service for generating CSV and JSON exports of scan results.

Requirements: 8.1, 8.2, 8.3, 8.4
"""
import csv
import json
from io import StringIO
from datetime import datetime
from typing import Any

from app.models.scan import Scan, ScanResult


class ExportService:
    """Service for exporting scan results in various formats.
    
    Supports CSV and JSON export with scan metadata.
    Requirements: 8.1, 8.2, 8.3, 8.4
    """

    @staticmethod
    def _format_datetime(dt: datetime | None) -> str | None:
        """Format datetime to ISO 8601 string."""
        if dt is None:
            return None
        return dt.isoformat()

    @staticmethod
    def _get_scan_metadata(scan: Scan) -> dict[str, Any]:
        """Extract scan metadata for export.
        
        Requirements: 8.3 - Include scan metadata
        """
        return {
            "scan_id": str(scan.id),
            "video_id": scan.video_id,
            "video_title": scan.video_title,
            "channel_name": scan.channel_name,
            "total_comments": scan.total_comments,
            "gambling_count": scan.gambling_count,
            "clean_count": scan.clean_count,
            "status": scan.status,
            "scanned_at": ExportService._format_datetime(scan.scanned_at),
            "created_at": ExportService._format_datetime(scan.created_at),
        }

    def export_csv(self, scan: Scan, results: list[ScanResult]) -> str:
        """Export scan results as CSV.
        
        Requirements: 8.1, 8.3
        - Generate CSV with required columns (comment_id, text, author, is_gambling, confidence)
        - Include scan metadata header
        
        Args:
            scan: The Scan object containing metadata
            results: List of ScanResult objects to export
            
        Returns:
            CSV string with metadata header and results
        """
        output = StringIO()
        
        # Write metadata header as comments
        metadata = self._get_scan_metadata(scan)
        output.write("# Scan Export\n")
        output.write(f"# scan_id: {metadata['scan_id']}\n")
        output.write(f"# video_id: {metadata['video_id']}\n")
        output.write(f"# video_title: {metadata['video_title']}\n")
        output.write(f"# channel_name: {metadata['channel_name']}\n")
        output.write(f"# total_comments: {metadata['total_comments']}\n")
        output.write(f"# gambling_count: {metadata['gambling_count']}\n")
        output.write(f"# clean_count: {metadata['clean_count']}\n")
        output.write(f"# scanned_at: {metadata['scanned_at']}\n")
        output.write(f"# created_at: {metadata['created_at']}\n")
        
        # Write CSV data with required columns
        writer = csv.writer(output)
        writer.writerow(["comment_id", "text", "author", "is_gambling", "confidence"])
        
        for result in results:
            writer.writerow([
                result.comment_id,
                result.comment_text or "",
                result.author_name or "",
                result.is_gambling,
                result.confidence,
            ])
        
        return output.getvalue()

    def export_json(self, scan: Scan, results: list[ScanResult]) -> str:
        """Export scan results as JSON.
        
        Requirements: 8.2, 8.3, 8.4
        - Generate JSON with complete scan results and metadata
        - Ensure valid JSON structure
        - Produce output that can be parsed back to equivalent data structures
        
        Args:
            scan: The Scan object containing metadata
            results: List of ScanResult objects to export
            
        Returns:
            JSON string with metadata and results
        """
        export_data = {
            "metadata": self._get_scan_metadata(scan),
            "results": [
                {
                    "comment_id": result.comment_id,
                    "text": result.comment_text,
                    "author": result.author_name,
                    "is_gambling": result.is_gambling,
                    "confidence": result.confidence,
                }
                for result in results
            ]
        }
        
        return json.dumps(export_data, ensure_ascii=False, indent=2)

    def parse_csv(self, csv_content: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """Parse CSV export back to metadata and results.
        
        Requirements: 8.4 - Round-trip consistency
        
        Args:
            csv_content: CSV string from export_csv
            
        Returns:
            Tuple of (metadata dict, list of result dicts)
        """
        lines = csv_content.strip().split("\n")
        metadata: dict[str, Any] = {}
        data_lines: list[str] = []
        
        for line in lines:
            if line.startswith("# ") and ": " in line:
                # Parse metadata from comment lines
                key_value = line[2:]  # Remove "# "
                key, value = key_value.split(": ", 1)
                # Convert types appropriately
                if key in ("total_comments", "gambling_count", "clean_count"):
                    metadata[key] = int(value) if value != "None" else 0
                elif value == "None":
                    metadata[key] = None
                else:
                    metadata[key] = value
            elif not line.startswith("#"):
                data_lines.append(line)
        
        # Parse CSV data
        results: list[dict[str, Any]] = []
        if data_lines:
            reader = csv.DictReader(data_lines)
            for row in reader:
                results.append({
                    "comment_id": row["comment_id"],
                    "text": row["text"] if row["text"] else None,
                    "author": row["author"] if row["author"] else None,
                    "is_gambling": row["is_gambling"] == "True",
                    "confidence": float(row["confidence"]),
                })
        
        return metadata, results

    def parse_json(self, json_content: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """Parse JSON export back to metadata and results.
        
        Requirements: 8.4 - Round-trip consistency
        
        Args:
            json_content: JSON string from export_json
            
        Returns:
            Tuple of (metadata dict, list of result dicts)
        """
        data = json.loads(json_content)
        return data["metadata"], data["results"]
