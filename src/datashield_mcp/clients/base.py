import random
import io
import base64
from typing import Any

from pathlib import Path
from mcp.types import ImageContent, TextContent
from datashield_mcp.models import DSContext
from datashield_mcp.logs import logger

import matplotlib

matplotlib.use("Agg")  # must be before importing pyplot
import matplotlib.pyplot as plt


class BaseClient:
    def __init__(self, dscontext: DSContext):
        """
        Service for performing statistical operations on DataSHIELD sessions.

        Args:
            dscontext: The DataSHIELD session context to use for performing operations
        """
        self.dscontext = dscontext

    def get_classes(self, symbol: str) -> dict[str, list[str]]:
        """
        Get the classes of a symbol in the remote R sessions for a given DataSHIELD session.

        Args:
            symbol: The symbol name to get the classes of in the remote R sessions
        Returns:
            A dictionary mapping server names to the classes of the specified symbol in the remote R sessions
        """
        classes = self.dscontext.session.aggregate(f"classDS('{symbol}')")
        logger.debug(f"[{self.dscontext.id}] Class for symbol '{symbol}': {classes}")
        # Make sure classes are lists (in case of single class, it might be returned as a string)
        for server, cls in classes.items():
            if isinstance(cls, str):
                classes[server] = [cls]
        return classes

    def get_length(self, symbol: str) -> dict[str, int]:
        """
        Get the length of a symbol in the remote R sessions for a given DataSHIELD session.

        Args:
            symbol: The symbol name to get the length of in the remote R sessions
        Returns:
            A dictionary mapping server names to the length of the specified symbol in the remote R sessions
        """
        lengths = self.dscontext.session.aggregate(f"lengthDS({symbol})")
        logger.info(f"[{self.dscontext.id}] Length for symbol '{symbol}': {lengths}")
        return lengths

    def get_levels(self, symbol: str) -> dict[str, list[str]]:
        """
        Get the levels of a factor symbol in the remote R sessions for a given DataSHIELD session.

        Args:
            symbol: The symbol name to get the levels of in the remote R sessions
        Returns:
            A dictionary mapping server names to the levels of the specified factor symbol in the remote R sessions
        """
        levels = self.dscontext.session.aggregate(f"levelsDS('{symbol}')")
        logger.info(f"[{self.dscontext.id}] Levels for symbol '{symbol}': {levels}")
        return levels

    def get_dimensions(self, symbol: str) -> dict[str, list[int]]:
        """
        Get the dimensions of a data.frame or matrix symbol in the remote R sessions for a given DataSHIELD session.

        Args:
            symbol: The symbol name to get the dimensions of in the remote R sessions
        Returns:
            A dictionary mapping server names to the dimensions of the specified data.frame or matrix symbol in the remote R sessions
        """
        dims = self.dscontext.session.aggregate(f"dimDS('{symbol}')")
        logger.info(f"[{self.dscontext.id}] Dimensions for symbol '{symbol}': {dims}")
        # Make sure dimensions are lists of integers
        for server, dim in dims.items():
            if dim is None:
                dims[server] = []
        return dims

    def get_frequencies(self, symbol: str) -> dict[str, Any]:
        """
        Get the frequencies of a factor or logical symbol in the remote R sessions for a given DataSHIELD session.

        Args:
            symbol: The symbol name to get the frequencies of in the remote R sessions
        Returns:
            A dictionary mapping server names to the frequencies of the specified factor or logical symbol in the remote R sessions
        """
        frequencies = self.dscontext.session.aggregate(f"table1DDS({symbol})")
        logger.info(f"[{self.dscontext.id}] Frequencies for symbol '{symbol}': {frequencies}")
        return frequencies

    def get_quantile_means(self, symbol: str) -> dict[str, Any]:
        """
        Get the quantiles and mean of a numeric or integer symbol in the remote R sessions for a given DataSHIELD session.

        Args:
            symbol: The symbol name to get the quantiles and mean of in the remote R sessions
        Returns:
            A dictionary mapping server names to the quantiles and mean of the specified numeric or integer symbol in the remote R sessions
        """
        quantile_means = self.dscontext.session.aggregate(f"quantileMeanDS({symbol})")
        logger.info(f"[{self.dscontext.id}] Quantiles and means for symbol '{symbol}': {quantile_means}")
        return quantile_means

    def get_names(self, symbol: str) -> dict[str, list[str]]:
        """
        Get the names of a list symbol in the remote R sessions for a given DataSHIELD session.

        Args:
            symbol: The symbol name to get the names of in the remote R sessions
        Returns:
            A dictionary mapping server names to the names of the specified list symbol in the remote R sessions
        """
        names = self.dscontext.session.aggregate(f"namesDS('{symbol}')")
        logger.info(f"[{self.dscontext.id}] Names for symbol '{symbol}': {names}")
        return names

    def is_valid(self, symbol: str) -> dict[str, bool]:
        """
        Check the validity of a symbol in the remote R sessions for a given DataSHIELD session.

        Args:
            symbol: The symbol name to check the validity of in the remote R sessions
        Returns:
            A dictionary mapping server names to the validity of the specified symbol in the remote R sessions
        """
        validity = self.dscontext.session.aggregate(f"isValidDS({symbol})")
        logger.info(f"[{self.dscontext.id}] Validity for symbol '{symbol}': {validity}")
        return validity

    def get_summary(self, symbol: str) -> dict[str, Any]:
        """
        Get the summary of a symbol in the remote R sessions for a given DataSHIELD session.

        Args:
            symbol: The symbol name to get the summary of in the remote R sessions
        Returns:
            A dictionary mapping server names to the summary of the specified symbol in the remote R sessions
        """
        classes = self.get_unique_classes(symbol)

        validity = self.is_valid(symbol)

        if "data.frame" in classes or "matrix" in classes:
            logger.debug(f"[{self.dscontext.id}] Symbol '{symbol}' is a data.frame or matrix")
            dims = self.get_dimensions(symbol)
            cols = self.dscontext.session.aggregate(f"colnamesDS('{symbol}')")
            summaries = {}
            for server in validity:
                summaries[server] = {
                    "validity": validity[server],
                    "dimensions": {
                        "rows": dims[server][0] if len(dims[server]) > 0 else 0,
                        "columns": dims[server][1] if len(dims[server]) > 1 else 0,
                    },
                    "columns": cols[server],
                }
            logger.debug(f"[{self.dscontext.id}] Summary for symbol '{symbol}': {summaries}")
            return summaries

        if "character" in classes:
            logger.debug(f"[{self.dscontext.id}] Symbol '{symbol}' is character")
            length = self.get_length(symbol)
            summaries = {}
            for server in validity:
                summaries[server] = {
                    "validity": validity[server],
                    "length": length[server],
                }
            logger.debug(f"[{self.dscontext.id}] Summary for symbol '{symbol}': {summaries}")
            return summaries

        if "factor" in classes:
            logger.debug(f"[{self.dscontext.id}] Symbol '{symbol}' is factor")
            length = self.get_length(symbol)
            levels = self.get_levels(symbol)
            frequencies = self.get_frequencies(symbol)
            summaries = {}
            for server in validity:
                summaries[server] = {
                    "validity": validity[server],
                    "length": length[server],
                    "levels": levels[server],
                    "frequencies": frequencies[server],
                }
            logger.debug(f"[{self.dscontext.id}] Summary for symbol '{symbol}': {summaries}")
            return summaries

        if "numeric" in classes or "integer" in classes:
            logger.debug(f"[{self.dscontext.id}] Symbol '{symbol}' is numeric or integer")
            length = self.get_length(symbol)
            quantile_means = self.get_quantile_means(symbol)
            summaries = {}
            for server in validity:
                summaries[server] = {
                    "validity": validity[server],
                    "length": length[server],
                    "quantile_means": quantile_means[server],
                }
            logger.debug(f"[{self.dscontext.id}] Summary for symbol '{symbol}': {summaries}")
            return summaries

        if "list" in classes:
            logger.debug(f"[{self.dscontext.id}] Symbol '{symbol}' is list")
            length = self.get_length(symbol)
            names = self.get_names(symbol)
            summaries = {}
            for server in validity:
                summaries[server] = {
                    "validity": validity[server],
                    "length": length[server],
                    "names": names[server],
                }
            logger.debug(f"[{self.dscontext.id}] Summary for symbol '{symbol}': {summaries}")
            return summaries

        if "logical" in classes:
            logger.debug(f"[{self.dscontext.id}] Symbol '{symbol}' is logical")
            length = self.get_length(symbol)
            frequencies = self.get_frequencies(symbol)
            summaries = {}
            for server in validity:
                summaries[server] = {
                    "validity": validity[server],
                    "length": length[server],
                    "frequencies": frequencies[server],
                }
            logger.debug(f"[{self.dscontext.id}] Summary for symbol '{symbol}': {summaries}")
            return summaries

        summaries = {}
        for server in validity:
            summaries[server] = {
                "validity": validity[server],
            }
        logger.debug(f"[{self.dscontext.id}] Summary for symbol '{symbol}': {summaries}")
        return summaries

    def get_mean(self, symbol: str) -> dict[str, Any]:
        """
        Get the mean of a symbol in the remote R sessions for a given DataSHIELD session.

        Args:
            symbol: The symbol name to get the mean of in the remote R sessions
        Returns:
            A dictionary mapping server names to the mean value of the specified symbol in the remote R sessions
        """
        means = self.dscontext.session.aggregate(f"meanDS({symbol})")
        logger.info(f"[{self.dscontext.id}] Mean for symbol '{symbol}': {means}")
        return means

    def get_histogram(self, symbol: str) -> list[TextContent | ImageContent]:
        """
        Get the histogram of a symbol in the remote R sessions for a given DataSHIELD session.

        Args:
            symbol: The symbol name to get the histogram of in the remote R sessions
        Returns:
            A list of TextContent and ImageContent objects representing the histogram and metadata for the specified symbol in the remote R sessions
        """
        data = self.dscontext.session.aggregate(
            f"histogramDS2({symbol}, num.breaks=20, min=0, max=20, method.indicator=1, k=3, noise=0.25)"
        )
        fig, ax = plt.subplots()
        for server, hist in data.items():
            logger.info(f"[{self.dscontext.id}] Histogram for symbol '{symbol}' on server '{server}': {hist}")
            breaks = hist["value"][0]["value"][0]["value"]
            counts = hist["value"][0]["value"][1]["value"]
            # random color
            color = (random.random(), random.random(), random.random(), 0.5)
            ax.bar(breaks[1:], counts, width=1, edgecolor="black", linewidth=0.5, alpha=0.5, label=server, color=color)
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

    def get_unique_classes(self, symbol: str) -> list[str]:
        """
        Get the unique classes of a symbol in the remote R sessions for a given DataSHIELD session.

        Args:
            symbol: The symbol name to get the unique classes of in the remote R sessions
        Returns:
            The unique classes of the specified symbol in the remote R sessions
        Raises:
            ValueError: If the specified symbol has multiple classes across servers
        """
        classes = self.get_classes(symbol)
        # Make sure class is unique accross servers
        the_classes = set()
        for _, cls in classes.items():
            for c in cls:
                the_classes.add(c)
        return list(the_classes)
