# -*- coding: utf-8 -*-

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from prefect.backend.flow_run import FlowView

from simmate.database.base_data_types import DatabaseTable
from simmate import workflows as workflow_module
from simmate.workflows.utilities import (
    # WORKFLOW_TYPES,
    get_workflow,
    get_list_of_workflows_by_type,
    parse_parameters,
)
from simmate.website.workflows.forms import SubmitWorkflow
from simmate.website.core_components.base_api_view import SimmateAPIViewSet


def workflows_all(request):

    # TODO: maybe instead load these descriptions from the simmate.{module}'s docstr
    # This would look something like...
    # all_metadata = {}
    # for flow_type in WORKFLOW_TYPES:
    #     --> grab the module
    #     --> use the __doc__ as the text.

    workflows_metadata = {
        "static-energy": (
            "These workflows calculate the energy for a structure. In many cases, "
            "this also involves calculating the lattice strain and forces for each site."
        ),
        "relaxation": (
            "These workflows geometry-optimize a structure's the lattice and sites "
            "until specified covergence criteria are met."
        ),
        "population-analysis": (
            "These workflows evaluate where electrons exist in a structure -- and "
            "they are often assigned to a specific site/atom. As a result of assigning "
            "electrons, these workflows give predicted oxidation states for each site."
        ),
        "band-structure": (
            "These workflows calculate the electronic band structure for a material."
        ),
        "density-of-states": (
            "These workflows calculate the electronic density of states for a material."
        ),
        "dynamics": (
            "These workflows run a molecular dynamics simulation for a material. This "
            "often involves iteratively evaluating the energy/forces of structure at "
            "specific temperature (or temperature ramp)."
        ),
        "diffusion": (
            "These workflows evaluate the diffusion of an atom through a material. "
            "At this time, these workflows are entirely Nudged-Elastic-Band (NEB) "
            "calculations."
        ),
    }

    # now let's put the data and template together to send the user
    context = {"workflows_metadata": workflows_metadata}
    template = "workflows/all.html"
    return render(request, template, context)


def workflows_by_type(request, workflow_type):

    workflow_names = get_list_of_workflows_by_type(workflow_type)

    workflow_type_module = getattr(workflow_module, workflow_type.replace("-", "_"))

    # pull the information together for each individual flow
    workflows = [get_workflow(n) for n in workflow_names]

    # now let's put the data and template together to send the user
    context = {
        "workflow_type": workflow_type,
        "workflow_type_description_short": workflow_type_module.__doc__,
        "workflows": workflows,
    }
    template = "workflows/by_type.html"
    return render(request, template, context)


class WorkflowAPIViewSet(SimmateAPIViewSet):

    template_list = "workflows/detail.html"
    template_retrieve = "workflows/detail_run.html"

    @classmethod
    def get_table(
        cls,
        request,
        workflow_type,
        workflow_name,
        pk=None,
    ) -> DatabaseTable:
        """
        grabs the relevant database table using the URL request
        """
        workflow_name_full = workflow_type + "/" + workflow_name
        workflow = get_workflow(workflow_name_full)
        return workflow.result_table

    def get_list_context(
        self,
        request,
        workflow_type,
        workflow_name,
    ) -> dict:

        workflow_name_full = workflow_type + "/" + workflow_name
        workflow = get_workflow(workflow_name_full)

        # In order to make links to the monitoring pages for each of these, we need
        # to grab the prefect id
        # If no flow exists in Prefect cloud, a ValueError is raised, so I can't
        # share this info
        try:
            flow_id = FlowView.from_flow_name(workflow_name_full).flow_id
            nflows_submitted = workflow.nflows_submitted
        except:  # ValueError is no query result. Need to test what error is if no API key.
            flow_id = None
            nflows_submitted = None
        # TODO: grab some metadata about this calc. For example...
        # ncalculations = MITRelaxation.objects.count()

        return {
            "workflow": workflow,
            "flow_id": flow_id,
            "nflows_submitted": nflows_submitted,
        }

    def get_retrieve_context(
        self,
        request,
        workflow_type,
        workflow_name,
        pk,
    ) -> dict:

        workflow_name_full = workflow_type + "/" + workflow_name
        workflow = get_workflow(workflow_name_full)

        return {"workflow": workflow}


@login_required
def workflow_submit(
    request,
    workflow_type: str,
    workflow_name: str,
):

    workflow_name_full = workflow_type + "/" + workflow_name
    workflow = get_workflow(workflow_name_full)

    # dynamically create the form for this workflow
    FormClass = SubmitWorkflow.from_workflow(workflow)

    if request.method == "POST":
        submission_form = FormClass(request.POST, request.FILES)

        # raise Exception(str(submission_form.errors))

        if submission_form.is_valid():

            # raise Exception("TEST123")

            parameters = parse_parameters(**submission_form.cleaned_data)

            # use parse_parameters util?

            # grab the structure (as a pymatgen object) and all other inputs
            # structure = submission_form.cleaned_data["structure_file"]
            # labels = submission_form.cleaned_data["labels"]
            # vasp_command = submission_form.cleaned_data["vasp_command"]

            # We can now submit the workflow for the structure.
            flow_run_id = workflow.run_cloud(wait_for_run=False, **parameters)

            return redirect(f"https://cloud.prefect.io/simmate/flow-run/{flow_run_id}")
    else:
        submission_form = FormClass()
    # now let's put the data and template together to send the user
    context = {
        "workflow": workflow,
        "submission_form": submission_form,
    }
    template = "workflows/submit.html"
    return render(request, template, context)
