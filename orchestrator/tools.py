"""Motion generation tool wrapping the keyword stub."""

from inference.stub import generate_motion_stub
from orchestrator.schemas import MotionExport, MotionRequest

def generate_motion(request: MotionRequest) -> MotionExport | None:
    return generate_motion_stub(request)