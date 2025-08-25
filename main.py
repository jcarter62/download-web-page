from fastapi import FastAPI
from dotenv import load_dotenv
import os
import httpx
from fastapi.responses import FileResponse, HTMLResponse

app = FastAPI()

load_dotenv()  # Load environment variables from .env file


@app.get("/download")
async def download_file():
    url = os.getenv("DOWNLOAD_PAGE")
    if not url:
        return {"error": "DOWNLOAD_PAGE environment variable is not set."}

    # calculate destination file name based on today's date
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    prefix = os.getenv("PAGE_PREFIX", "delta_ops_summary_")
    postfix = os.getenv("PAGE_POSTFIX", ".pdf")
    destination_file = f"{prefix}{today}{postfix}"
    # add DESTINATION_FOLDER to the destination file path.
    destination_folder = os.getenv("DESTINATION_FOLDER", ".")
    #
    destination_file = os.path.join(destination_folder, destination_file)
    #
    # create destination folder if it does not exist
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)
    #
    msg = ""
    #
    # download the file using url, and save it to destination_file

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            with open(destination_file, "wb") as f:
                f.write(response.content)
        msg = "File downloaded successfully."
    except Exception as e:
        msg = "error: " + str(e)

    return {"message": msg}


def generate_style():
    return """
    <style>
        body { font-size: 1.75vw; font-family: math; }
        li:nth-child(odd) { background: #f0f0f0; }
    </style>
    """

@app.get("/", response_class=HTMLResponse)
@app.get("/files", response_class=HTMLResponse)
async def list_files(page: int = 1):
    folder = os.getenv("DESTINATION_FOLDER")
    if not folder:
        return "<p>DESTINATION_FOLDER environment variable is not set.</p>"
    if not os.path.exists(folder):
        return f"<p>Folder {folder} does not exist.</p>"
    files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
    files.sort(reverse=True)
    page_size = int(os.getenv("PAGE_SIZE", 20))
    title = os.getenv("PAGE_TITLE", "Files in folder")
    total_files = len(files)
    total_pages = (total_files + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    files_page = files[start:end]
    html = ''
    html += generate_style()
    html += f"<h2>{title} (Page {page} of {total_pages})</h2><ul>"
    for file in files_page:
        html += f'<li><a href="/download_file?filename={file}">{file}</a></li>'
    html += "</ul>"
    # Add paging controls
    html += "<div style='margin-top:20px;'>"
    if page > 1:
        html += f'<a href="/files?page={page-1}">Previous</a> '
    if page < total_pages:
        html += f'<a href="/files?page={page+1}">Next</a>'
    html += "</div>"
    return html

@app.get("/download_file")
async def download_file_by_name(filename: str):
    folder = os.getenv("DESTINATION_FOLDER")
    if not folder:
        return {"error": "DESTINATION_FOLDER environment variable is not set."}
    file_path = os.path.join(folder, filename)
    if not os.path.exists(file_path):
        return {"error": f"File {filename} not found."}
    return FileResponse(path=file_path, filename=filename, media_type='application/octet-stream')

