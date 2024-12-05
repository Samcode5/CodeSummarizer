from pathlib import Path
from typing import List, Dict
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import re

class PDFGenerator:
    def __init__(self):
        """Initialize PDF styles and configuration"""
        self.styles = getSampleStyleSheet()
        # Create custom styles
        self.styles.add(ParagraphStyle(
            name='FileHeader',
            parent=self.styles['Heading1'],
            fontSize=14,
            spaceAfter=20
        ))
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceAfter=10
        ))
        self.styles.add(ParagraphStyle(
            name='CodeText',
            parent=self.styles['BodyText'],
            fontName='Courier',
            fontSize=9,
            leftIndent=20
        ))

    def _clean_markdown(self, text: str) -> str:
        """Clean markdown formatting for PDF compatibility"""
        # Remove color codes if present
        text = re.sub(r'\x1b\[[0-9;]*m', '', text)
        
        # Replace markdown headers
        text = re.sub(r'#{1,6}\s+', '', text)
        
        # Replace bold
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        
        # Replace italic
        text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
        
        # Replace bullet points
        text = re.sub(r'^\s*[\-\*]\s+', '• ', text, flags=re.MULTILINE)
        
        # Replace code blocks
        text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)
        
        # Clean any remaining special characters
        text = text.replace('\\', '')
        
        return text

    def create_pdf_summary(self, summaries: List[tuple[str, str]], output_path: Path, 
                          directory_name: str, stats: Dict) -> None:
        """Create a PDF report from the code summaries."""
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        story = []

        # Title
        title = Paragraph(f"Code Analysis Report - {directory_name}", self.styles['Title'])
        story.append(title)
        story.append(Spacer(1, 20))

        # Generation Information
        story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                             self.styles['Normal']))
        story.append(Spacer(1, 20))

        # Statistics Table
        stats_data = [
            ["Processing Statistics", ""],
            ["Total Files", str(stats['total'])],
            ["Successfully Processed", str(stats['success'])],
            ["Skipped", str(stats['skipped'])],
            ["Failed", str(stats['failed'])]
        ]
        stats_table = Table(stats_data, colWidths=[2*inch, 1.5*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(stats_table)
        story.append(Spacer(1, 30))

        # Table of Contents
        toc_header = Paragraph("Table of Contents", self.styles['Heading1'])
        story.append(toc_header)
        story.append(Spacer(1, 10))

        for i, (filepath, _) in enumerate(summaries, 1):
            toc_entry = Paragraph(
                f"{i}. {filepath}",
                self.styles['Normal']
            )
            story.append(toc_entry)
            story.append(Spacer(1, 5))

        story.append(Spacer(1, 30))

        # File Summaries
        for filepath, summary in summaries:
            # File header
            file_header = Paragraph(
                f"File: {filepath}",
                self.styles['FileHeader']
            )
            story.append(file_header)

            # Clean and format the summary
            cleaned_summary = self._clean_markdown(summary)
            sections = cleaned_summary.split('\n\n')
            
            for section in sections:
                if section.strip():
                    try:
                        para = Paragraph(section.strip(), self.styles['Normal'])
                        story.append(para)
                        story.append(Spacer(1, 10))
                    except Exception as e:
                        print(f"Warning: Skipping problematic section in {filepath}")
                        continue

            story.append(Spacer(1, 20))

        # Build the PDF
        doc.build(story)