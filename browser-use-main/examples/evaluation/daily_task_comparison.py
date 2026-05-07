"""CLI wrapper for the daily task evaluation module.

The implementation lives in `browser_use.experiments.daily_task_eval` so it can be reused
as a pluggable module without editing core agent code.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from browser_use.experiments.daily_task_eval.models import TaskCard, load_json_model_list, write_json
from browser_use.experiments.daily_task_eval.navigator import NavigatorConfig
from browser_use.experiments.daily_task_eval.runner import compare_all, init_experiment, run_agent_task


async def run_agent_command(args: argparse.Namespace) -> None:
	tasks = load_json_model_list(Path(args.task_cards), TaskCard)
	selected_tasks = [task for task in tasks if args.task_id in (None, task.id)]
	if not selected_tasks:
		raise ValueError(f'No task card matched task id: {args.task_id}')

	agent_runs_path = Path(args.output_dir) / 'agent_runs.json'
	existing_runs = []
	if agent_runs_path.exists():
		existing_runs = json.loads(agent_runs_path.read_text(encoding='utf-8'))

	navigator_config = NavigatorConfig(
		enabled=args.use_navigator,
		model=args.navigator_model,
		api_key_env=args.navigator_api_key_env,
		base_url=args.navigator_base_url,
	)

	for task in selected_tasks:
		summary = await run_agent_task(
			task=task,
			output_dir=Path(args.output_dir),
			scenario_id=args.scenario_id,
			max_steps=args.max_steps,
			headless=args.headless,
			navigator_config=navigator_config,
		)
		existing_runs.append(summary.model_dump(mode='json'))
		write_json(agent_runs_path, existing_runs)
		print(f'Wrote Agent run summary for {task.id}/{args.scenario_id} to {agent_runs_path}')


def build_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(description='Run human-vs-Agent daily task comparison experiments.')
	subparsers = parser.add_subparsers(dest='command', required=True)

	init_parser = subparsers.add_parser('init', help='Create starter task cards and result files.')
	init_parser.add_argument('--output-dir', type=Path, default=Path('./tmp/daily_task_eval'))
	init_parser.add_argument('--overwrite', action='store_true')

	run_parser = subparsers.add_parser('run-agent', help='Run Browser Use Agent for one or more task cards.')
	run_parser.add_argument('--task-cards', type=Path, default=Path('./tmp/daily_task_eval/task_cards.json'))
	run_parser.add_argument('--output-dir', type=Path, default=Path('./tmp/daily_task_eval'))
	run_parser.add_argument('--task-id', default=None)
	run_parser.add_argument('--scenario-id', default='normal')
	run_parser.add_argument('--max-steps', type=int, default=30)
	run_parser.add_argument('--headless', action='store_true')
	run_parser.add_argument(
		'--use-navigator', action='store_true', help='Ask a navigator model to draft a plan before execution.'
	)
	run_parser.add_argument('--navigator-model', default='qwen3-max')
	run_parser.add_argument('--navigator-api-key-env', default='ALIBABA_CLOUD')
	run_parser.add_argument('--navigator-base-url', default='https://dashscope-intl.aliyuncs.com/compatible-mode/v1')

	compare_parser = subparsers.add_parser('compare', help='Compare human baselines with Agent run summaries.')
	compare_parser.add_argument('--task-cards', type=Path, default=Path('./tmp/daily_task_eval/task_cards.json'))
	compare_parser.add_argument('--human-runs', type=Path, default=Path('./tmp/daily_task_eval/human_runs.json'))
	compare_parser.add_argument('--agent-runs', type=Path, default=Path('./tmp/daily_task_eval/agent_runs.json'))
	compare_parser.add_argument('--output-path', type=Path, default=Path('./tmp/daily_task_eval/comparison_report.json'))

	return parser


def main() -> None:
	parser = build_parser()
	args = parser.parse_args()

	if args.command == 'init':
		paths = init_experiment(args.output_dir, overwrite=args.overwrite)
		for name, path in paths.items():
			print(f'{name}: {path}')
	elif args.command == 'run-agent':
		asyncio.run(run_agent_command(args))
	elif args.command == 'compare':
		comparisons = compare_all(args.task_cards, args.human_runs, args.agent_runs, args.output_path)
		print(f'Wrote {len(comparisons)} comparison record(s) to {args.output_path}')
	else:
		raise ValueError(f'Unknown command: {args.command}')


if __name__ == '__main__':
	main()
