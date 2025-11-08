import io
import matplotlib

# Use a non-interactive backend (required when no display is available)
matplotlib.use("Agg")

from fastapi import FastAPI, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# --- FastAPI App Initialization ---
app = FastAPI(title="Pyplot Code Executor API", description="An API that executes Matplotlib code and returns a PNG image.")

# Allow cross-origin requests from local frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Pydantic Model for Request Body ---
# This defines the expected structure of the JSON payload
class PyplotCode(BaseModel):
    code: str


# --- The API Endpoint ---
@app.post("/generate-graph/")
async def generate_graph(payload: PyplotCode):
    """
    Executes raw Python code that uses Matplotlib (pyplot) to generate a graph.
    Returns the graph as a PNG image byte array.
    """

    # Create an in-memory binary stream to save the image to.
    # This avoids saving a file to disk on the server.
    image_buffer = io.BytesIO()

    # Define the execution scope for the user's code.
    # We provide common libraries like plt, np, and pd so the user's code
    # doesn't have to import them.
    execution_globals = {
        "plt": plt,
        "np": np,
        "pd": pd,
    }

    try:
        # The DANGEROUS part: executing arbitrary code.
        exec(payload.code, execution_globals)

        # Save the current figure created by the executed code to the buffer.
        # We specify the format as 'png'.
        plt.savefig(image_buffer, format="png", bbox_inches="tight")

        # Move the buffer's cursor to the beginning to be read.
        image_buffer.seek(0)

        # Return the image as a response.
        # The media_type 'image/png' tells the browser to render it as an image.
        return Response(content=image_buffer.getvalue(), media_type="image/png")

    except Exception as e:
        # If the user's code fails, return a 400 error with the exception message.
        # This helps with debugging on the frontend.
        raise HTTPException(status_code=400, detail=f"Error executing code: {e}")
    finally:
        # IMPORTANT: Clear the current figure to free up memory and prevent
        # plots from bleeding into subsequent requests.
        plt.close("all")
