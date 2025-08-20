from .base import Base, TimestampMixin

# Ensure all models are imported so their tables are registered in Base.metadata
# These imports are for side effects (table definitions); exported names remain limited via __all__
from .models import app_user  # noqa: F401
from .models import app_user_session  # noqa: F401
from .models import app_user_role  # noqa: F401
from .models import role  # noqa: F401
from .models import permission  # noqa: F401
from .models import role_permission  # noqa: F401
from .models import ref_state  # noqa: F401
from .models import organization  # noqa: F401
from .models import person  # noqa: F401
from .models import qualification  # noqa: F401
from .models import person_qualification  # noqa: F401
from .models import team  # noqa: F401
from .models import team_role  # noqa: F401
from .models import person_team  # noqa: F401
from .models import subject  # noqa: F401
from .models import case  # noqa: F401
from .models import team_case  # noqa: F401
from .models import app_user_case  # noqa: F401
from .models import ref_relation  # noqa: F401
from .models import ref_sm_platform  # noqa: F401
from .models import ref_activity  # noqa: F401
from .models import ref_file_type  # noqa: F401
from .models import ref_scope  # noqa: F401
from .models import ref_case_classification  # noqa: F401
from .models import ref_status  # noqa: F401
from .models import ref_requested_by  # noqa: F401
from .models import ref_alive  # noqa: F401
from .models import ref_ministry  # noqa: F401
from .models import ref_actions  # noqa: F401
from .models import ref_found_by  # noqa: F401
from .models import ref_intel_discover  # noqa: F401
from .models import ref_exploitation  # noqa: F401
from .models import ref_sub_relation  # noqa: F401
from .models import person_case  # noqa: F401
from .models import social_media  # noqa: F401
from .models import timeline  # noqa: F401
from .models import activity  # noqa: F401
from .models import message  # noqa: F401
from .models import file  # noqa: F401
from .models import file_person  # noqa: F401
from .models import subject_case  # noqa: F401

__all__ = ["Base", "TimestampMixin"]
