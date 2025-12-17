import markdown
from xhtml2pdf import pisa
import io
import os

def create_pdf_report(markdown_content, output_path="reports/project_pipeline_report.pdf"):
    """
    Converts the provided markdown content into a styled PDF report.
    Uses xhtml2pdf as a pure-Python alternative to WeasyPrint.
    """
    print(f"Generating PDF report from markdown content...")

    # Convert markdown table to an HTML string
    html_body = markdown.markdown(markdown_content, extensions=['tables'])

    # Basic HTML template
    html_template = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Helvetica, sans-serif; font-size: 12px; }}
            h1 {{ color: #333; text-align: center; font-size: 18px; margin-bottom: 20px; }}
            table {{ width: 100%; border: 1px solid #ddd; border-collapse: collapse; margin-top: 10px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; font-weight: bold; }}
        </style>
    </head>
    <body>
        {html_body}
    </body>
    </html>
    """

    # Ensure the output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Generate the PDF
    with open(output_path, "wb") as pdf_file:
        pisa_status = pisa.CreatePDF(io.StringIO(html_template), dest=pdf_file)

    if pisa_status.err:
        print(f"Error generating PDF: {pisa_status.err}")
    else:
        print(f"Successfully generated PDF report: {output_path}")

if __name__ == '__main__':
    # Test execution
    report_markdown = """
    # Test Report
    | Column 1 | Column 2 |
    | :--- | :--- |
    | Value A | Value B |
    """
    create_pdf_report(report_markdown)