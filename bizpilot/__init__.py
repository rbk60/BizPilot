"""
BizPilot: AI Business Operating System.
An orchestration framework for collaborative AI agents analyzing businesses and generating strategies.
"""

import httpx
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Global monkey-patch to bypass local SSL issues
_orig_init = httpx.Client.__init__
def _patched_init(self, *args, **kwargs):
    kwargs['verify'] = False
    _orig_init(self, *args, **kwargs)
httpx.Client.__init__ = _patched_init

_orig_async_init = httpx.AsyncClient.__init__
def _patched_async_init(self, *args, **kwargs):
    kwargs['verify'] = False
    _orig_async_init(self, *args, **kwargs)
httpx.AsyncClient.__init__ = _patched_async_init

__version__ = "0.1.0"

from bizpilot.agents.core.agent import core_agent as root_agent
