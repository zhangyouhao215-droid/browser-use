from __future__ import annotations

from .models import TaskCard


def list_items(items: list[str]) -> list[str]:
	if not items:
		return ['- Not specified.']
	return [f'- {item}' for item in items]


def build_agent_task_prompt(task: TaskCard, scenario_id: str = 'normal', navigator_plan: str | None = None) -> str:
	scenario = next((failure for failure in task.failure_modes if failure.id == scenario_id), None)
	lines = [
		f'Task: {task.name}',
		'',
		task.task_prompt,
		'',
		'Starting conditions:',
		*list_items(task.starting_conditions),
		'',
		'Success criteria:',
		*list_items(task.success_criteria),
		'',
		'Forbidden actions:',
		*list_items(task.forbidden_actions),
		'',
		'Recovery rules:',
		*list_items(task.agent_recovery_rules),
	]
	if scenario:
		lines.extend(
			[
				'',
				f'Failure scenario under test: {scenario.name}',
				'Expected recovery:',
				*list_items(scenario.expected_recovery),
			]
		)
	if navigator_plan:
		lines.extend(
			[
				'',
				'Navigator plan:',
				navigator_plan,
				'',
				'Use the navigator plan as guidance, but trust the live page state over stale assumptions.',
			]
		)
	lines.extend(
		[
			'',
			'When the task is complete, call done with a concise final result. '
			'If blocked, call done with success=False and explain the blocker.',
		]
	)
	return '\n'.join(lines)


def build_navigator_prompt(task: TaskCard, scenario_id: str = 'normal') -> str:
	scenario = next((failure for failure in task.failure_modes if failure.id == scenario_id), None)
	lines = [
		'Create an execution plan for a browser automation agent.',
		'You are the navigator, not the executor. Do not claim that you opened the browser.',
		'Return concise markdown with these sections: Assumptions, Step-by-step plan, Recovery plan, Stop conditions.',
		'',
		f'Task id: {task.id}',
		f'Task name: {task.name}',
		'',
		'Task prompt:',
		task.task_prompt,
		'',
		'Starting conditions:',
		*list_items(task.starting_conditions),
		'',
		'Success criteria:',
		*list_items(task.success_criteria),
		'',
		'Forbidden actions:',
		*list_items(task.forbidden_actions),
		'',
		'Existing recovery rules:',
		*list_items(task.agent_recovery_rules),
	]
	if scenario:
		lines.extend(
			[
				'',
				f'Failure scenario under test: {scenario.name}',
				'Failure setup notes:',
				*list_items(scenario.setup_notes),
				'Expected recovery:',
				*list_items(scenario.expected_recovery),
			]
		)
	return '\n'.join(lines)

