import random
import io
import base64

from pathlib import Path
from mcp.types import ImageContent, TextContent
from datashield_mcp.models import DSContext
from datashield_mcp.logs import logger

import matplotlib

matplotlib.use("Agg")  # must be before importing pyplot
import matplotlib.pyplot as plt


class PlotsClient:
    """Service for performing plotting operations on DataSHIELD sessions.

    This client provides methods for generating plots based on data in remote R sessions of a DataSHIELD session.
    The generated plots are saved to files in the .datashield/work/<session_id> directory and also returned as
    base64-encoded image data that can be displayed in the client application.
    """

    def __init__(self, dscontext: DSContext):
        """
        Service for performing plotting operations on DataSHIELD sessions.

        Args:
            dscontext: The DataSHIELD session context to use for performing operations
        """
        self.dscontext = dscontext

    def get_histogram(
        self, symbol: str, num_breaks: int = 20, k: int = 3, noise: float = 0.25
    ) -> list[TextContent | ImageContent]:
        """
        Get the histogram of a symbol in the remote R sessions for a given DataSHIELD session.

        Args:
            symbol: The symbol name to get the histogram of in the remote R sessions
            num_breaks: The number of breaks to use for the histogram (default is 20)
            k: The number of the nearest neighbours for which their centroid is calculated (default is 3)
            noise: The noise parameter for the histogram (default is 0.25)
        Returns:
            A list of TextContent and ImageContent objects representing the histogram and metadata for the specified symbol in the remote R sessions
        """
        # Find min,max values across servers to use for consistent breaks
        ranges = self.dscontext.session.aggregate(f"histogramDS1({symbol}, method.indicator=1, k={k}, noise={noise})")
        min = None
        max = None
        for server, range in ranges.items():
            logger.info(f"[{self.dscontext.id}] Range for symbol '{symbol}' on server '{server}': {range}")
            if range is not None and len(range) == 2:
                server_min, server_max = range
                if min is None or server_min < min:
                    min = server_min
                if max is None or server_max > max:
                    max = server_max
        if min is None or max is None:
            raise ValueError(f"Could not determine min and max values for symbol '{symbol}' across servers")
        # floor min to nearest integer and ceil max to nearest integer for better breaks
        min = int(min) if min == int(min) else int(min) - 1
        # ceil max to nearest integer
        max = int(max) + 1 if max == int(max) else int(max) + 1
        data = self.dscontext.session.aggregate(
            f"histogramDS2({symbol}, num.breaks={num_breaks}, min={min}, max={max}, method.indicator=1, k={k}, noise={noise})"
        )
        fig, ax = plt.subplots()
        for server, hist in data.items():
            logger.info(f"[{self.dscontext.id}] Histogram for symbol '{symbol}' on server '{server}': {hist}")
            breaks = hist["value"][0]["value"][0]["value"]
            counts = hist["value"][0]["value"][1]["value"]
            # Calculate bin width from breaks
            bin_width = breaks[1] - breaks[0] if len(breaks) > 1 else 1
            # random color
            color = (random.random(), random.random(), random.random(), 0.5)
            ax.bar(
                breaks[1:],
                counts,
                width=bin_width,
                edgecolor="black",
                linewidth=0.5,
                alpha=0.5,
                label=server,
                color=color,
            )
        ax.set_xlabel("Value")
        ax.set_ylabel("Frequency")
        ax.set_title(f"Histogram of {symbol}")
        ax.legend()

        # Save to file in .datashield/work/<session_id>
        work_dir = Path.cwd() / ".datashield" / "work" / self.dscontext.id
        work_dir.mkdir(parents=True, exist_ok=True)
        # Generate filename from symbol (replace special chars)
        safe_symbol = symbol.replace("$", "_").replace("/", "_").replace("\\", "_")
        output_path = work_dir / f"histogram_{safe_symbol}.png"
        fig.savefig(output_path, format="png", bbox_inches="tight")
        logger.info(f"[{self.dscontext.id}] Saved histogram to {output_path}")

        # Save to bytes buffer
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight")
        plt.close(fig)  # important — avoid memory leaks
        buf.seek(0)
        image_b64 = base64.b64encode(buf.read()).decode("utf-8")

        image_url = f"plot://{self.dscontext.id}/histogram_{safe_symbol}"

        return [
            TextContent(
                type="text",
                text=f"Histogram of {symbol} saved to {output_path} (url is {image_url})",
            ),
            ImageContent(type="image", data=image_b64, mimeType="image/png"),
        ]
