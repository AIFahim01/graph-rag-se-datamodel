"""
Enhanced Metadata Extractor for HVDC/SynCon Projects
Extracts customer, project, technology metadata from folder structures and content
"""

import re
from pathlib import Path
from typing import Dict, Optional


class MetadataExtractor:
    """Extract rich metadata for Neo4j vector storage queries"""

    # Known customers from HVDC/SynCon projects
    CUSTOMERS = [
        'TenneT', 'RTE', 'SEC', 'Transgrid', 'ITC', 'Xcel', 'Powerlink',
        'Siemens', 'ABB', 'Hitachi', 'GE', 'Alstom', 'KEPCO',
        'SingaporePower', 'GridUnited', 'Agora', 'LS Power'
    ]

    # Technology types
    TECHNOLOGIES = {
        'VSC': 'Voltage Source Converter',
        'LCC': 'Line Commutated Converter',
        'MMC': 'Modular Multilevel Converter',
        'SynCon': 'Synchronous Condenser'
    }

    def extract_from_folder(self, folder_path: Path) -> Dict[str, str]:
        """
        Extract metadata from GC25 folder structure

        Example: GC25_084_HVDC_VSC_Lanwin4_Tennet
        Returns: {
            'project_id': 'GC25_084',
            'project_type': 'HVDC',
            'technology': 'VSC',
            'project_name': 'Lanwin4',
            'customer': 'TenneT'
        }
        """
        folder_name = folder_path.name
        parts = folder_name.split('_')

        metadata = {
            'project_id': 'Unknown',
            'project_type': 'Unknown',
            'technology': 'Unknown',
            'project_name': folder_name,
            'customer': 'Unknown',
            'category': 'unknown'
        }

        # Extract project ID (GC25_XXX)
        if len(parts) >= 2 and parts[0].startswith('GC'):
            metadata['project_id'] = f"{parts[0]}_{parts[1]}"

        # Extract project type (HVDC or SynCon)
        for part in parts:
            if 'HVDC' in part.upper():
                metadata['project_type'] = 'HVDC'
                metadata['category'] = 'hvdc'
                break
            elif 'SYNCON' in part.upper():
                metadata['project_type'] = 'SynCon'
                metadata['category'] = 'syncon'
                break

        # Extract technology (VSC, LCC, MMC)
        for tech in self.TECHNOLOGIES.keys():
            if tech in folder_name.upper():
                metadata['technology'] = tech
                break

        # Extract customer name
        customer = self.extract_customer(folder_name, "")
        if customer:
            metadata['customer'] = customer
            metadata['customer_normalized'] = customer.lower()

        return metadata

    def extract_customer(self, text: str, content: str = "") -> Optional[str]:
        """
        Extract customer name from text or content

        Priority:
        1. Check folder/filename for customer patterns
        2. If not found, search content
        """
        # Check text (folder name or filename) first
        text_upper = text.upper()

        for customer in self.CUSTOMERS:
            customer_upper = customer.upper()

            # Exact match or as part of word
            if customer_upper in text_upper:
                # Check if it's a word boundary match
                pattern = r'\b' + re.escape(customer) + r'\b'
                if re.search(pattern, text, re.IGNORECASE):
                    return customer
                # Also accept as part of compound name
                elif customer_upper in text_upper:
                    return customer

        # If not found in filename, search content
        if content:
            content_sample = content[:5000]  # Check first 5000 chars
            for customer in self.CUSTOMERS:
                pattern = r'\b' + re.escape(customer) + r'\b'
                if re.search(pattern, content_sample, re.IGNORECASE):
                    return customer

        return None

    def extract_document_type(self, filename: str) -> str:
        """Classify document type from filename"""
        filename_lower = filename.lower()

        if any(kw in filename_lower for kw in ['pricing', 'commercial', 'offer', 'proposal']):
            return 'commercial'
        elif any(kw in filename_lower for kw in ['technical', 'spec', 'study', 'analysis', 'design']):
            return 'technical'
        elif any(kw in filename_lower for kw in ['contract', 'agreement', 'terms']):
            return 'contractual'
        else:
            return 'other'

    def enrich_chunk_metadata(self, chunk: Dict, project_folder: Path, filename: str) -> Dict:
        """
        Enrich chunk with full metadata

        Args:
            chunk: Base chunk with text, page, etc.
            project_folder: Path to GC25_XXX folder
            filename: Source PDF filename

        Returns:
            Enriched chunk with metadata for Neo4j
        """
        # Extract project-level metadata
        project_metadata = self.extract_from_folder(project_folder)

        # Extract document-level metadata
        doc_type = self.extract_document_type(filename)

        # If customer not found in folder, try filename
        if project_metadata['customer'] == 'Unknown':
            customer = self.extract_customer(filename, chunk.get('text', ''))
            if customer:
                project_metadata['customer'] = customer
                project_metadata['customer_normalized'] = customer.lower()

        # Merge all metadata
        enriched = {
            **chunk,
            **project_metadata,
            'document_type': doc_type,
            'source_file': filename
        }

        return enriched
