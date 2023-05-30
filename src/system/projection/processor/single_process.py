"""
:class:`~src.system.projection.Projection` processing, using a single process.
"""

from tqdm import tqdm

from src.system.projection.processor import ProjectionProcessor
from src.system.projection.parameters import ProjectionParameters
from src.system.logger import Logger


class SingleProcessProjectionProcessor(
    ProjectionProcessor
):

    """
    :class:`~src.system.projection.processor.ProjectionProcessor` that calculates
    :class:`Projections <src.system.projection.Projection>` using a single process. Useful for debugging.
    """

    def __init__(
        self,
        projection_parameters: ProjectionParameters
    ):

        ProjectionProcessor.__init__(
            self=self,
            projection_parameters=projection_parameters
        )

    def run_projections(
        self
    ) -> None:

        """
        Loops through and runs :class:`projections <src.system.projection.Projection>`, until
        all projections are calculated.

        :return: Nothing.
        """

        Logger().print(message='Running projections ...')

        projections = tqdm(self.projections, desc=r'Progress: ', unit=r' projection(s) ')

        for projection in projections:

            self.run_projection(
                projection=projection
            )
