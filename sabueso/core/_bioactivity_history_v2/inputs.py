"""Inert SDK202 inputs, retaining the unchanged scientific SDK200 predicates."""

from .._bioactivity_history_v1.inputs import _CapturedCard as _OriginalCard
from .._bioactivity_history_v1.inputs import _FrozenAccess as _FrozenAccess


class _CapturedCard(_OriginalCard):
    def literature(self):
        from .._literature_history_v1.literature import literature_view

        return literature_view(self)

    def explain_literature(self, publication_ref):
        from .._literature_history_v1.literature_explanation import explain_literature

        return explain_literature(self, publication_ref)
