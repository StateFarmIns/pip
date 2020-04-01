from pip._internal.utils.typing import MYPY_CHECK_RUNNING

from .candidates import ExtrasCandidate, LinkCandidate, RequiresPythonCandidate
from .requirements import (
    ExplicitRequirement,
    NoMatchRequirement,
    SpecifierRequirement,
)

if MYPY_CHECK_RUNNING:
    from typing import Dict, Optional, Set, Tuple

    from pip._vendor.packaging.specifiers import SpecifierSet

    from pip._internal.index.package_finder import PackageFinder
    from pip._internal.models.link import Link
    from pip._internal.operations.prepare import RequirementPreparer
    from pip._internal.req.req_install import InstallRequirement
    from pip._internal.resolution.base import InstallRequirementProvider

    from .base import Candidate, Requirement


class Factory(object):
    def __init__(
        self,
        finder,  # type: PackageFinder
        preparer,  # type: RequirementPreparer
        make_install_req,  # type: InstallRequirementProvider
        ignore_requires_python,  # type: bool
        py_version_info=None,  # type: Optional[Tuple[int, ...]]
    ):
        # type: (...) -> None
        self.finder = finder
        self.preparer = preparer
        self._python_candidate = RequiresPythonCandidate(py_version_info)
        self._ignore_requires_python = ignore_requires_python
        self._make_install_req_from_spec = make_install_req
        self._candidate_cache = {}  # type: Dict[Link, LinkCandidate]

    def make_candidate(
        self,
        link,    # type: Link
        extras,  # type: Set[str]
        parent,  # type: InstallRequirement
    ):
        # type: (...) -> Candidate
        if link not in self._candidate_cache:
            self._candidate_cache[link] = LinkCandidate(
                link, parent, factory=self,
            )
        base = self._candidate_cache[link]
        if extras:
            return ExtrasCandidate(base, extras)
        return base

    def make_requirement_from_install_req(self, ireq):
        # type: (InstallRequirement) -> Requirement
        if ireq.link:
            cand = self.make_candidate(ireq.link, extras=set(), parent=ireq)
            return ExplicitRequirement(cand)
        else:
            return SpecifierRequirement(ireq, factory=self)

    def make_requirement_from_spec(self, specifier, comes_from):
        # type: (str, InstallRequirement) -> Requirement
        ireq = self._make_install_req_from_spec(specifier, comes_from)
        return self.make_requirement_from_install_req(ireq)

    def make_requires_python_requirement(self, specifier):
        # type: (Optional[SpecifierSet]) -> Optional[Requirement]
        if self._ignore_requires_python or specifier is None:
            return None
        if self._python_candidate.version in specifier:
            return ExplicitRequirement(self._python_candidate)
        return NoMatchRequirement(self._python_candidate.name)
