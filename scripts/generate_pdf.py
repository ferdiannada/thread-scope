import os
import subprocess
import markdown_it

md_path = "/home/nutrisari/Project/web/threads-scraping/DOKUMENTASI_ILMIAH_SISTEM.md"
html_path = "/tmp/dokumentasi_ilmiah.html"
pdf_path = "/home/nutrisari/Project/web/threads-scraping/DOKUMENTASI_ILMIAH_SISTEM.pdf"

with open(md_path, "r", encoding="utf-8") as f:
    text = f.read()

# Setup markdown-it parser
md = markdown_it.MarkdownIt("commonmark").enable(["table", "strikethrough"])
rendered_body = md.render(text)

html_template = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="utf-8">
<title>Dokumentasi Ilmiah dan Teknis Sistem Karhutla Threads Scraping</title>
<style>
  @page {{
    size: A4;
    margin: 22mm 18mm 22mm 18mm;
    @bottom-center {{
      content: "Halaman " counter(page);
      font-size: 8.5pt;
      color: #64748b;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }}
  }}
  
  * {{
    box-sizing: border-box;
  }}

  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 10pt;
    line-height: 1.6;
    color: #1e293b;
    background-color: #ffffff;
    margin: 0;
    padding: 0;
  }}

  h1 {{
    font-size: 18pt;
    font-weight: 700;
    color: #0f172a;
    border-bottom: 2px solid #0284c7;
    padding-bottom: 6px;
    margin-top: 24pt;
    margin-bottom: 12pt;
    page-break-after: avoid;
  }}

  h2 {{
    font-size: 13.5pt;
    font-weight: 700;
    color: #0f172a;
    border-bottom: 1px solid #cbd5e1;
    padding-bottom: 4px;
    margin-top: 18pt;
    margin-bottom: 10pt;
    page-break-after: avoid;
  }}

  h3 {{
    font-size: 11pt;
    font-weight: 600;
    color: #1e293b;
    margin-top: 14pt;
    margin-bottom: 6pt;
    page-break-after: avoid;
  }}

  h4 {{
    font-size: 10pt;
    font-weight: 600;
    color: #334155;
    margin-top: 10pt;
    margin-bottom: 4pt;
    page-break-after: avoid;
  }}

  p {{
    margin-top: 0;
    margin-bottom: 8pt;
    text-align: justify;
  }}

  strong {{
    color: #0f172a;
  }}

  hr {{
    border: none;
    border-top: 1px solid #e2e8f0;
    margin: 16pt 0;
  }}

  ul, ol {{
    margin-top: 0;
    margin-bottom: 8pt;
    padding-left: 20px;
  }}

  li {{
    margin-bottom: 3pt;
  }}

  code {{
    font-family: "JetBrains Mono", "Fira Code", Consolas, Monaco, "Courier New", monospace;
    font-size: 8.5pt;
    background-color: #f1f5f9;
    color: #0369a1;
    padding: 1px 4px;
    border-radius: 3px;
    border: 1px solid #e2e8f0;
  }}

  pre {{
    background-color: #0f172a;
    color: #f8fafc;
    padding: 10pt 12pt;
    border-radius: 5px;
    font-family: "JetBrains Mono", "Fira Code", Consolas, Monaco, "Courier New", monospace;
    font-size: 8pt;
    line-height: 1.45;
    overflow-x: hidden;
    white-space: pre-wrap;
    word-break: break-all;
    margin-top: 6pt;
    margin-bottom: 10pt;
    page-break-inside: avoid;
  }}

  pre code {{
    background-color: transparent;
    color: #f8fafc;
    padding: 0;
    border: none;
    font-size: inherit;
  }}

  table {{
    width: 100%;
    border-collapse: collapse;
    margin-top: 8pt;
    margin-bottom: 12pt;
    font-size: 8.5pt;
    page-break-inside: avoid;
  }}

  th, td {{
    border: 1px solid #cbd5e1;
    padding: 5pt 7pt;
    text-align: left;
    vertical-align: top;
  }}

  th {{
    background-color: #f8fafc;
    color: #0f172a;
    font-weight: 600;
  }}

  tr:nth-child(even) td {{
    background-color: #fcfcfd;
  }}

  blockquote {{
    border-left: 3px solid #0284c7;
    margin: 8pt 0;
    padding: 4pt 10pt;
    background-color: #f0f9ff;
    color: #0c4a6e;
    font-style: italic;
  }}

  .doc-header {{
    text-align: center;
    border-bottom: 2px solid #0f172a;
    padding-bottom: 14pt;
    margin-bottom: 18pt;
  }}

  .doc-header h1 {{
    border-bottom: none;
    margin-top: 0;
    margin-bottom: 4pt;
    color: #0f172a;
    font-size: 19pt;
  }}

  .doc-subtitle {{
    font-size: 11pt;
    color: #475569;
    font-weight: 500;
    margin-bottom: 6pt;
  }}

  .doc-meta {{
    font-size: 8.5pt;
    color: #64748b;
  }}
</style>
</head>
<body>
{rendered_body}
</body>
</html>
"""

with open(html_path, "w", encoding="utf-8") as f:
    f.write(html_template)

print("HTML generated successfully at", html_path)

cmd = [
    "google-chrome",
    "--headless=new",
    "--no-sandbox",
    "--disable-gpu",
    "--disable-software-rasterizer",
    f"--print-to-pdf={pdf_path}",
    "--print-to-pdf-no-header",
    html_path,
]

res = subprocess.run(cmd, capture_output=True, text=True)
print("Chrome stdout:", res.stdout)
print("Chrome stderr:", res.stderr)
if os.path.exists(pdf_path):
    size_kb = os.path.getsize(pdf_path) / 1024
    print(f"SUCCESS: PDF created at {pdf_path} ({size_kb:.1f} KB)")
else:
    print("ERROR: PDF file was not created.")
