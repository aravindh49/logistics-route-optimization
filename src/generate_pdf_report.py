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
            body {{ font-family: 'Open Sans', Helvetica, sans-serif; font-size: 14px; color: #1c1c1c; padding: 20px; }}
            h1 {{ color: #020617; text-align: left; font-size: 24px; padding-bottom: 5px; border-bottom: 2px solid #0ea5e9; margin-bottom: 25px; }}
            h2 {{ color: #0f172a; font-size: 18px; margin-top: 20px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; border-radius: 8px; overflow: hidden; }}
            th, td {{ border: 1px solid #e2e8f0; padding: 12px; text-align: left; }}
            th {{ background-color: #f1f5f9; font-weight: bold; color: #0f172a; font-size: 13px; text-transform: uppercase; }}
            td {{ background-color: #ffffff; color: #334155; }}
            blockquote {{ background-color: #f8fafc; border-left: 4px solid #0ea5e9; padding: 10px 15px; margin: 20px 0; font-style: italic; color: #64748b; font-size: 13px; }}
            strong {{ color: #020617; }}
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