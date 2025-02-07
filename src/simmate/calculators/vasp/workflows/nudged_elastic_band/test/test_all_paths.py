# -*- coding: utf-8 -*-

import pytest

from simmate.conftest import copy_test_files

from simmate.calculators.vasp.inputs import Potcar
from simmate.workflow_engine import S3Task

from simmate.calculators.vasp.workflows.nudged_elastic_band import all_paths_workflow


@pytest.mark.django_db
def test_neb(sample_structures, tmpdir, mocker):
    copy_test_files(
        tmpdir,
        test_directory=__file__,
        test_folder="all_paths",
    )

    # For testing, look at I- diffusion in Y2CF2
    structure = sample_structures["Y2CI2_mp-1206803_primitive"]

    # Because we won't have POTCARs accessible, we need to cover this function
    # call -- specifically have it pretend to make a file
    mocker.patch.object(Potcar, "to_file_from_type", return_value=None)

    # We also don't want to run any commands -- for any task. We skip these
    # by having the base S3task.execute just return an empty list (meaning
    # no corrections were made).
    mocker.patch.object(S3Task, "execute", return_value=[])

    # run the workflow and make sure it handles data properly.
    state = all_paths_workflow.run(
        structure=structure,
        migrating_specie="I",
        command="dummycmd1; dummycmd2; dummycmd3",
        directory=str(tmpdir),
    )
    assert state.is_successful()
