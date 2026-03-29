import random
import io
import base64
import math
from statistics import NormalDist
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

    def get_glm(
        self,
        formula: str = None,
        family: str = None,
        offset: str = None,
        weights: str = None,
        data: str = None,
        maxit: int = 20,
        CI: float = 0.95,
        viewIter: bool = False,
        viewVarCov: bool = False,
        viewCor: bool = False,
    ) -> dict[str, Any]:
        """Get the generalized linear model (GLM) results for a specified formula and family in the remote R sessions for a given DataSHIELD session.

        Args:
            formula: The formula to use for the GLM (e.g., "y ~ x1 + x2") (default is None)
            family: The family to use for the GLM (e.g., "gaussian", "binomial", "poisson") (default is None)
            offset: The offset variable to use for the GLM (default is None)
            weights: The weights variable to use for the GLM (default is None)
            data: The data frame to use for the GLM (default is None)
            maxit: The maximum number of iterations for the GLM fitting process (default is 20)
            CI: The confidence interval level to use for the GLM results (default is 0.95)
            viewIter: Whether to include the iteration details in the GLM results (default is False)
            viewVarCov: Whether to include the variance-covariance matrix in the GLM results (default is False)
            viewCor: Whether to include the correlation matrix in the GLM results (default is False)
        Returns:
            A dictionary mapping server names to the GLM results for the specified formula and family in the remote R sessions
        Raises:
            ValueError: If the specified formula or family is invalid
        """
        if formula is None:
            raise ValueError("Please provide a valid regression formula!")

        if family is None:
            raise ValueError("Please provide a valid 'family' argument!")

        formula_text = str(formula)
        family_text = str(family).strip().lower()
        if family_text not in {"gaussian", "binomial", "poisson"}:
            raise ValueError("family must be one of: gaussian, binomial, poisson")

        if "offset" in formula_text.lower() or "weights" in formula_text.lower():
            logger.warning(
                "[%s] offset/weights appears in formula; in ds.glm these are expected as separate arguments",
                self.dscontext.id,
            )

        if maxit <= 0:
            raise ValueError("maxit must be a positive integer")

        if CI < 0:
            raise ValueError("CI must be >= 0")

        # Internal helpers to support both named-list and positional list payloads.
        def _unwrap_value(obj: Any) -> Any:
            while isinstance(obj, dict) and set(obj.keys()) == {"value"}:
                obj = obj["value"]
            return obj

        def _named_or_index(obj: Any, name: str, idx: int | None = None) -> Any:
            obj = _unwrap_value(obj)
            if isinstance(obj, dict):
                if name in obj:
                    return _unwrap_value(obj[name])
                if idx is not None and "value" in obj and isinstance(obj["value"], list) and idx < len(obj["value"]):
                    return _unwrap_value(obj["value"][idx])
            if isinstance(obj, list) and idx is not None and idx < len(obj):
                return _unwrap_value(obj[idx])
            return None

        def _as_float_vector(obj: Any) -> list[float]:
            obj = _unwrap_value(obj)
            if obj is None:
                return []
            if isinstance(obj, (int, float)):
                return [float(obj)]
            if isinstance(obj, list):
                result: list[float] = []
                for x in obj:
                    xv = _unwrap_value(x)
                    if isinstance(xv, (int, float)):
                        result.append(float(xv))
                return result
            return []

        def _as_float_matrix(obj: Any) -> list[list[float]]:
            obj = _unwrap_value(obj)
            if obj is None:
                return []
            if isinstance(obj, list):
                rows: list[list[float]] = []
                for row in obj:
                    row_v = _unwrap_value(row)
                    if isinstance(row_v, list):
                        rows.append([float(_unwrap_value(v)) for v in row_v])
                return rows
            return []

        def _call_glm_ds1() -> dict[str, Any]:
            formula_expr = formula_text.strip()
            # If callers pass a quoted formula string, unwrap one quote layer so R receives a formula expression.
            if len(formula_expr) >= 2 and formula_expr[0] == formula_expr[-1] and formula_expr[0] in {"'", '"'}:
                formula_expr = formula_expr[1:-1]
            family_expr = repr(family_text)
            weights_expr = "NULL" if weights is None else repr(str(weights))
            offset_expr = "NULL" if offset is None else repr(str(offset))
            data_expr = "NULL" if data is None else repr(str(data))
            expr = f"glmDS1({formula_expr}, {family_expr}, {weights_expr}, {offset_expr}, {data_expr})"
            rval = self.dscontext.session.aggregate(expr)
            logger.debug(f"[{self.dscontext.id}] GLM DS1 result: {rval}")
            return rval

        def _call_glm_ds2(beta_csv: str) -> dict[str, Any]:
            formula_expr = formula_text.strip()
            if len(formula_expr) >= 2 and formula_expr[0] == formula_expr[-1] and formula_expr[0] in {"'", '"'}:
                formula_expr = formula_expr[1:-1]
            family_expr = repr(family_text)
            beta_expr = repr(beta_csv)
            offset_expr = "NULL" if offset is None else repr(str(offset))
            weights_expr = "NULL" if weights is None else repr(str(weights))
            data_expr = "NULL" if data is None else repr(str(data))
            expr = f"glmDS2({formula_expr}, {family_expr}, {beta_expr}, {offset_expr}, {weights_expr}, {data_expr})"
            rval = self.dscontext.session.aggregate(expr)
            logger.debug(f"[{self.dscontext.id}] GLM DS2 result: {rval}")
            return rval

        study_summary_0 = _call_glm_ds1()
        servers = list(study_summary_0.keys())
        if not servers:
            raise ValueError("No DataSHIELD servers available for GLM analysis")

        first = _unwrap_value(study_summary_0[servers[0]])
        first_meta = _named_or_index(first, "", 0)

        num_par = None
        num_par_candidates = [
            _named_or_index(first_meta, "num.par.glm", None),
            _named_or_index(first_meta, "num_par_glm", None),
            _named_or_index(first_meta, "", 1),
            _named_or_index(first, "num.par.glm", None),
            _named_or_index(first, "num_par_glm", None),
        ]
        for candidate in num_par_candidates:
            if candidate is not None:
                num_par = candidate
                break

        coef_names_raw = _named_or_index(first, "coef.names", None)
        if coef_names_raw is None:
            coef_names_raw = _named_or_index(first, "coef_names", None)
        if coef_names_raw is None:
            coef_names_raw = _named_or_index(first, "", 1)

        try:
            num_par_glm = int(num_par) if num_par is not None else 0
        except (TypeError, ValueError):
            num_par_glm = 0

        coef_names = []
        if isinstance(coef_names_raw, list):
            coef_names = [str(_unwrap_value(x)) for x in coef_names_raw]

        y_invalid: dict[str, int] = {}
        x_invalid: dict[str, list[float]] = {}
        w_invalid: dict[str, int] = {}
        o_invalid: dict[str, int] = {}
        glm_saturation_invalid: dict[str, int] = {}
        error_message_first: dict[str, Any] = {}

        at_least_one_study_data_error = False
        for server, summary in study_summary_0.items():
            entry = _unwrap_value(summary)
            error_msg = _named_or_index(entry, "errorMessage", 7)
            error_message_first[server] = error_msg
            if error_msg != "No errors":
                at_least_one_study_data_error = True

            y_invalid[server] = int(_named_or_index(entry, "", 2) or 0)
            x_invalid[server] = _as_float_vector(_named_or_index(entry, "", 3))
            w_invalid[server] = int(_named_or_index(entry, "", 4) or 0)
            o_invalid[server] = int(_named_or_index(entry, "", 5) or 0)
            glm_saturation_invalid[server] = int(_named_or_index(entry, "", 6) or 0)

        sum_y_invalid = sum(y_invalid.values())
        sum_x_invalid = sum(sum(v) for v in x_invalid.values())
        sum_w_invalid = sum(w_invalid.values())
        sum_o_invalid = sum(o_invalid.values())
        sum_glm_saturation_invalid = sum(glm_saturation_invalid.values())

        if (
            sum_y_invalid > 0
            or sum_x_invalid > 0
            or sum_w_invalid > 0
            or sum_o_invalid > 0
            or sum_glm_saturation_invalid > 0
            or at_least_one_study_data_error
        ):
            logger.warning(
                "[%s] GLM fitting terminated at first iteration due to study validation errors", self.dscontext.id
            )
            return {
                "output.blocked.information.1": "MODEL FITTING TERMINATED AT FIRST ITERATION:",
                "output.blocked.information.2": "Any values of 1 in the following tables denote potential disclosure risks",
                "output.blocked.information.3": "please use the argument <datasources> to include only valid studies.",
                "output.blocked.information.4": "Errors by study are as follows:",
                "y.vector.error": y_invalid,
                "X.matrix.error": x_invalid,
                "weight.vector.error": w_invalid,
                "offset.vector.error": o_invalid,
                "glm.overparameterized": glm_saturation_invalid,
                "errorMessage": error_message_first,
            }

        if num_par_glm <= 0:
            num_par_glm = len(coef_names) if coef_names else 1

        beta_next = [0.0] * num_par_glm
        beta_csv = ",".join(str(x) for x in beta_next)

        dev_old = 9.99e99
        epsilon = 1.0e-08
        iteration_count = 0
        converge_state = False

        variance_covariance_matrix_total: list[list[float]] | None = None
        correlation: list[list[float]] | None = None
        score_vect_total: list[float] | None = None
        dev_total = 0.0
        nsubs_total = 0
        nvalid_total = 0
        nmissing_total = 0
        ntotal_total = 0
        disclosure_risk: dict[str, Any] = {}
        error_message_second: dict[str, Any] = {}
        family_info: Any = family_text

        while not converge_state and iteration_count < maxit:
            iteration_count += 1
            logger.info("[%s] GLM iteration %s", self.dscontext.id, iteration_count)

            study_summary = _call_glm_ds2(beta_csv)

            disclosure_risk = {}
            error_message_second = {}
            disclosure_risk_total = 0

            info_matrix_total = None
            score_total = None
            dev_total = 0.0
            nvalid_total = 0
            nmissing_total = 0
            ntotal_total = 0

            numsubs_iter = 0

            for server, summary in study_summary.items():
                entry = _unwrap_value(summary)

                risk_val = _named_or_index(entry, "disclosure.risk", 8)
                if risk_val is None:
                    risk_val = 0
                disclosure_risk[server] = risk_val
                try:
                    disclosure_risk_total += int(risk_val)
                except (TypeError, ValueError):
                    disclosure_risk_total += 0

                error_message_second[server] = _named_or_index(entry, "errorMessage", 9)

                info_matrix = _as_float_matrix(_named_or_index(entry, "info.matrix", None))
                if not info_matrix:
                    info_matrix = _as_float_matrix(_named_or_index(entry, "", 0))
                score_vect = _as_float_vector(_named_or_index(entry, "score.vect", None))
                if not score_vect:
                    score_vect = _as_float_vector(_named_or_index(entry, "", 1))

                if info_matrix_total is None:
                    info_matrix_total = [row[:] for row in info_matrix]
                else:
                    for i in range(min(len(info_matrix_total), len(info_matrix))):
                        for j in range(min(len(info_matrix_total[i]), len(info_matrix[i]))):
                            info_matrix_total[i][j] += info_matrix[i][j]

                if score_total is None:
                    score_total = score_vect[:]
                else:
                    for i in range(min(len(score_total), len(score_vect))):
                        score_total[i] += score_vect[i]

                dev_total += float(_named_or_index(entry, "dev", 2) or 0.0)
                nvalid_total += int(_named_or_index(entry, "Nvalid", 3) or 0)
                nmissing_total += int(_named_or_index(entry, "Nmissing", 4) or 0)
                ntotal_total += int(_named_or_index(entry, "Ntotal", 5) or 0)

                numsubs_iter += int(_named_or_index(entry, "numsubs", 6) or 0)

                fam = _named_or_index(entry, "family", 7)
                if fam is not None:
                    family_info = fam

            if disclosure_risk_total > 0:
                logger.error("[%s] Potential disclosure risk detected during GLM fit", self.dscontext.id)
                return {
                    "output.blocked.information.1": "Potential disclosure risk in y.vect, X.mat, w.vect or offset",
                    "output.blocked.information.2": "or model overparameterized in at least one study.",
                    "output.blocked.information.3": "In addition clientside function appears to have been modified",
                    "output.blocked.information.4": "to avoid disclosure traps in first serverside function.",
                    "output.blocked.information.5": "Score vectors and information matrices therefore destroyed in all invalid studies",
                    "output.blocked.information.6": "and model fitting terminated. This error is recorded in the log file but",
                    "output.blocked.information.7": "please also report it to the DataSHIELD team as we need to understand how",
                    "output.blocked.information.8": "the controlled shutdown traps in glmDS1 have been circumvented.",
                }

            if iteration_count == 1:
                nsubs_total = numsubs_iter

            if info_matrix_total is None or score_total is None:
                raise ValueError("No information matrix or score vector returned by server")

            # Solve info_matrix_total * beta_update = score_total.
            npar = len(info_matrix_total)
            aug = [
                row[:] + [score_total[i] if i < len(score_total) else 0.0] for i, row in enumerate(info_matrix_total)
            ]

            for col in range(npar):
                pivot = max(range(col, npar), key=lambda r: abs(aug[r][col]))
                if abs(aug[pivot][col]) < 1.0e-12:
                    raise ValueError("Information matrix is singular; cannot continue GLM fitting")
                if pivot != col:
                    aug[col], aug[pivot] = aug[pivot], aug[col]
                piv = aug[col][col]
                for j in range(col, npar + 1):
                    aug[col][j] /= piv
                for r in range(npar):
                    if r == col:
                        continue
                    factor = aug[r][col]
                    for j in range(col, npar + 1):
                        aug[r][j] -= factor * aug[col][j]

            beta_update = [aug[i][npar] for i in range(npar)]
            if iteration_count == 1:
                beta_next = [0.0] * len(beta_update)
            for i in range(min(len(beta_next), len(beta_update))):
                beta_next[i] += beta_update[i]
            beta_csv = ",".join(str(x) for x in beta_next)

            # Compute inverse(info_matrix_total) for output uncertainty matrices.
            inv_aug = [
                row[:] + [1.0 if i == j else 0.0 for j in range(npar)] for i, row in enumerate(info_matrix_total)
            ]
            for col in range(npar):
                pivot = max(range(col, npar), key=lambda r: abs(inv_aug[r][col]))
                if abs(inv_aug[pivot][col]) < 1.0e-12:
                    raise ValueError("Information matrix is singular; cannot compute covariance matrix")
                if pivot != col:
                    inv_aug[col], inv_aug[pivot] = inv_aug[pivot], inv_aug[col]
                piv = inv_aug[col][col]
                for j in range(col, 2 * npar):
                    inv_aug[col][j] /= piv
                for r in range(npar):
                    if r == col:
                        continue
                    factor = inv_aug[r][col]
                    for j in range(col, 2 * npar):
                        inv_aug[r][j] -= factor * inv_aug[col][j]

            variance_covariance_matrix_total = [row[npar:] for row in inv_aug]

            # Correlation matrix from variance-covariance.
            diag_sqrt = [
                math.sqrt(v) if v > 0 else 0.0 for v in (variance_covariance_matrix_total[i][i] for i in range(npar))
            ]
            correlation = []
            for i in range(npar):
                row = []
                for j in range(npar):
                    denom = diag_sqrt[i] * diag_sqrt[j]
                    row.append(variance_covariance_matrix_total[i][j] / denom if denom > 0 else 0.0)
                correlation.append(row)

            converge_value = abs(dev_total - dev_old) / (abs(dev_total) + 0.1)
            converge_state = converge_value <= epsilon
            if not converge_state:
                dev_old = dev_total

            if viewIter:
                logger.info(
                    "[%s] Iteration %s deviance=%s df=%s converge=%s (%s)",
                    self.dscontext.id,
                    iteration_count,
                    dev_total,
                    nsubs_total - len(beta_next),
                    converge_state,
                    converge_value,
                )

            score_vect_total = score_total

        if not converge_state:
            logger.warning(
                "[%s] Did not converge after %s iterations. Increase maxit parameter as necessary.",
                self.dscontext.id,
                maxit,
            )
            return None

        if variance_covariance_matrix_total is None or score_vect_total is None:
            raise ValueError("GLM fitting failed before covariance/statistics were available")

        scale_par = 1.0
        if family_text == "gaussian":
            denom = nsubs_total - len(beta_next)
            if denom > 0:
                scale_par = dev_total / denom

        se_vect_final = [
            math.sqrt(max(variance_covariance_matrix_total[i][i], 0.0)) * math.sqrt(scale_par)
            for i in range(len(beta_next))
        ]
        z_vect_final = [
            beta_next[i] / se_vect_final[i] if se_vect_final[i] != 0 else float("inf") for i in range(len(beta_next))
        ]

        norm = NormalDist()
        pval_vect_final = [2.0 * (1.0 - norm.cdf(abs(z))) for z in z_vect_final]

        if not coef_names or len(coef_names) != len(beta_next):
            coef_names = [f"beta_{i + 1}" for i in range(len(beta_next))]

        coefficients = []
        for i, name in enumerate(coef_names):
            coefficients.append({
                "name": name,
                "Estimate": beta_next[i],
                "Std. Error": se_vect_final[i],
                "z-value": z_vect_final[i],
                "p-value": pval_vect_final[i],
            })

        if CI > 0:
            ci_mult = norm.inv_cdf(1.0 - (1.0 - CI) / 2.0)
            for row in coefficients:
                est = row["Estimate"]
                se = row["Std. Error"]
                low_ci_lp = est - ci_mult * se
                high_ci_lp = est + ci_mult * se

                if family_text == "gaussian":
                    row[f"low{CI}CI"] = low_ci_lp
                    row[f"high{CI}CI"] = high_ci_lp
                elif family_text == "binomial":
                    row[f"low{CI}CI.LP"] = low_ci_lp
                    row[f"high{CI}CI.LP"] = high_ci_lp
                    row["P_OR"] = math.exp(est) / (1.0 + math.exp(est))
                    row[f"low{CI}CI.P_OR"] = math.exp(low_ci_lp) / (1.0 + math.exp(low_ci_lp))
                    row[f"high{CI}CI.P_OR"] = math.exp(high_ci_lp) / (1.0 + math.exp(high_ci_lp))
                elif family_text == "poisson":
                    row[f"low{CI}CI.LP"] = low_ci_lp
                    row[f"high{CI}CI.LP"] = high_ci_lp
                    row["EXPONENTIATED RR"] = math.exp(est)
                    row[f"low{CI}CI.EXP"] = math.exp(low_ci_lp)
                    row[f"high{CI}CI.EXP"] = math.exp(high_ci_lp)

        if offset is not None and weights is not None:
            formula_out = f"{formula_text} + offset({offset}) + weights({weights})"
        elif offset is not None:
            formula_out = f"{formula_text} + offset({offset})"
        elif weights is not None:
            formula_out = f"{formula_text} + weights({weights})"
        else:
            formula_out = formula_text

        result = {
            "Nvalid": nvalid_total,
            "Nmissing": nmissing_total,
            "Ntotal": ntotal_total,
            "disclosure.risk": disclosure_risk,
            "errorMessage": error_message_second,
            "nsubs": nsubs_total,
            "iter": iteration_count,
            "family": family_info,
            "formula": formula_out,
            "coefficients": coefficients,
            "dev": dev_total,
            "df": nsubs_total - len(beta_next),
            "output.information": "SEE TOP OF OUTPUT FOR INFORMATION ON MISSING DATA AND ERROR MESSAGES",
        }

        if viewVarCov:
            result["VarCovMatrix"] = variance_covariance_matrix_total
        if viewCor and correlation is not None:
            result["CorrMatrix"] = correlation

        logger.info("[%s] GLM completed in %s iteration(s)", self.dscontext.id, iteration_count)
        return result
