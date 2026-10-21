"""Contract tests with fake CUPS commands: no printer or CUPS service needed."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.bin = self.work / 'bin'
        self.bin.mkdir()
        self.log = self.work / 'calls.jsonl'
        self.stat_log = self.work / 'stat_calls.jsonl'
        self.ppd = self.work / 'trusted driver.ppd'
        # Only a header fixture; not a real driver and never sent to real CUPS.
        self.ppd.write_text('*PPD-Adobe: "4.3"\n', encoding='utf-8')
        self.env = dict(os.environ, PATH=f'{self.bin}:/usr/bin:/bin',
                        CALL_LOG=str(self.log), STAT_LOG=str(self.stat_log))
        self.fake('lpadmin', '''import json, os, sys
with open(os.environ['CALL_LOG'], 'a') as f:
    f.write(json.dumps(sys.argv[1:]) + '\\n')
sys.exit(int(os.environ.get('ADMIN_EXIT', '0')))
''')
        self.fake('lpstat', '''import json, os, sys
args = sys.argv[1:]
with open(os.environ['STAT_LOG'], 'a') as f:
    f.write(json.dumps(args) + '\\n')
# CUPS 2.4 can prefer LC_MESSAGES to LC_ALL when selecting messages.
language = os.environ.get('LC_MESSAGES', os.environ.get('LC_ALL', 'C'))
if '-r' in args:
    status = os.environ.get('SCHEDULER_STATUS', 'scheduler is running')
    if language not in ('C', 'POSIX'):
        status = 'el planificador esta funcionando'
    print(status)
    sys.exit(int(os.environ.get('SCHEDULER_EXIT', '0')))
if args[-1] == '-p':
    queues = os.environ.get('QUEUES', '')
    if language not in ('C', 'POSIX'):
        queues = queues.replace('printer ', 'impresora ')
    print(queues)
    sys.exit(int(os.environ.get('LIST_EXIT', '0')))
sys.exit(int(os.environ.get('VERIFY_EXIT', '0')))
''')

    def fake(self, name, source):
        path = self.bin / name
        path.write_text('#!/usr/bin/env python3\n' + source, encoding='utf-8')
        path.chmod(0o755)

    def run_cli(self, *args, env=None, script='install-printer.sh'):
        return subprocess.run(['bash', str(ROOT / script), *args],
                              env=env or self.env, text=True, capture_output=True,
                              timeout=10)

    def base(self):
        return ['--name', 'Oficina', '--uri', 'ipp://printer.local/ipp/print',
                '--driverless']

    def calls(self):
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def stat_calls(self):
        if not self.stat_log.exists():
            return []
        return [json.loads(line) for line in self.stat_log.read_text().splitlines()]

    def test_help(self):
        self.assertEqual(self.run_cli('--help').returncode, 0)
        self.assertFalse(self.calls())

    def test_version(self):
        self.assertEqual(self.run_cli('--version').stdout.strip(), '1.0.1')

    def test_missing_options(self):
        self.assertEqual(self.run_cli().returncode, 2)

    def test_missing_value(self):
        for args in [('--name',), ('--uri', '--driverless'), ('--ppd', '')]:
            with self.subTest(args=args):
                self.assertEqual(self.run_cli(*args).returncode, 2)

    def test_unknown_option(self):
        self.assertEqual(self.run_cli('--surprise').returncode, 2)

    def test_invalid_names(self):
        for name in ['two words', '-option', '../queue', 'a' * 128, '$(id)']:
            with self.subTest(name=name):
                args = self.base()
                args[1] = name
                self.assertEqual(self.run_cli(*args).returncode, 2)
        self.assertFalse(self.calls())

    def test_invalid_uris(self):
        for uri in ['https://printer', 'ipp://', 'ipp://user:pass@printer/q',
                    'ipp://printer/a b', 'ipp://printer/q?token=x',
                    'ipp://printer/q#fragment', 'ipp://printer/q\nanything']:
            with self.subTest(uri=uri):
                args = self.base()
                args[3] = uri
                self.assertEqual(self.run_cli(*args).returncode, 2)
        self.assertFalse(self.calls())

    def test_ipv6_and_ipps(self):
        args = self.base()
        args[3] = 'ipps://[2001:db8::1]:631/ipp/print'
        self.assertEqual(self.run_cli(*args, '--dry-run').returncode, 0)

    def test_driverless_requires_ipp(self):
        args = self.base()
        args[3] = 'socket://192.0.2.10:9100'
        self.assertEqual(self.run_cli(*args).returncode, 2)

    def test_driver_is_required(self):
        self.assertEqual(self.run_cli(*self.base()[:-1]).returncode, 2)

    def test_conflicting_drivers(self):
        self.assertEqual(self.run_cli(*self.base(), '--ppd', str(self.ppd)).returncode, 2)

    def test_missing_ppd(self):
        args = self.base()[:-1] + ['--ppd', str(self.work / 'missing.ppd')]
        self.assertEqual(self.run_cli(*args).returncode, 2)

    def test_invalid_ppd_header(self):
        self.ppd.write_text('not a PPD\n')
        args = self.base()[:-1] + ['--ppd', str(self.ppd)]
        self.assertEqual(self.run_cli(*args).returncode, 2)

    def test_dry_run_never_contacts_cups(self):
        env = dict(self.env, SCHEDULER_EXIT='1')
        result = self.run_cli(*self.base(), '--dry-run', env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('lpadmin', result.stdout)
        self.assertFalse(self.calls())
        self.assertFalse(self.stat_calls())

    def test_driverless_creates_only_requested_queue(self):
        result = self.run_cli(*self.base())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls(), [[
            '-h', 'localhost', '-p', 'Oficina', '-E', '-v',
            'ipp://printer.local/ipp/print', '-m', 'everywhere',
            '-o', 'printer-is-shared=false']])
        self.assertEqual(self.stat_calls(), [
            ['-h', 'localhost', '-r'],
            ['-h', 'localhost', '-p'],
            ['-h', 'localhost', '-p', 'Oficina']])

    def test_ppd_path_and_metadata_are_separate_arguments(self):
        args = ['--name', 'Taller', '--uri', 'lpd://192.0.2.10/print',
                '--ppd', str(self.ppd), '--description', 'Sharp del taller',
                '--location', 'Planta 1']
        result = self.run_cli(*args)
        self.assertEqual(result.returncode, 0, result.stderr)
        call = self.calls()[0]
        self.assertEqual(call[call.index('-P') + 1], str(self.ppd))
        self.assertEqual(call[call.index('-D') + 1], 'Sharp del taller')
        self.assertEqual(call[call.index('-L') + 1], 'Planta 1')

    def test_metadata_is_not_executed(self):
        marker = self.work / 'must-not-exist'
        text = f'$(touch {marker}); touch {marker}'
        result = self.run_cli(*self.base(), '--description', text)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(marker.exists())
        self.assertIn(text, self.calls()[0])

    def test_control_characters_in_metadata_are_rejected(self):
        self.assertEqual(self.run_cli(*self.base(), '--location', 'a\nb').returncode, 2)

    def test_existing_queue_is_protected_case_insensitively(self):
        env = dict(self.env, QUEUES='printer oficina is idle. enabled since today')
        self.assertEqual(self.run_cli(*self.base(), env=env).returncode, 4)
        self.assertFalse(self.calls())

    def test_explicit_update(self):
        env = dict(self.env, QUEUES='printer Oficina is idle.')
        result = self.run_cli(*self.base(), '--update', env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(self.calls()), 1)

    def test_scheduler_failure_stops_before_changes(self):
        env = dict(self.env, SCHEDULER_EXIT='1')
        self.assertEqual(self.run_cli(*self.base(), env=env).returncode, 3)
        self.assertFalse(self.calls())

    def test_stopped_scheduler_with_zero_exit_stops_before_changes(self):
        # Real lpstat -r returns zero even when the scheduler is stopped.
        env = dict(self.env, SCHEDULER_STATUS='scheduler is not running',
                   SCHEDULER_EXIT='0')
        result = self.run_cli(*self.base(), env=env)
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertFalse(self.calls())
        self.assertEqual(self.stat_calls(), [['-h', 'localhost', '-r']])

    def test_unrecognized_scheduler_status_stops_before_changes(self):
        for status in ['', 'unexpected response',
                       'scheduler is running\nscheduler is not running']:
            with self.subTest(status=status):
                env = dict(self.env, SCHEDULER_STATUS=status, SCHEDULER_EXIT='0')
                result = self.run_cli(*self.base(), env=env)
                self.assertEqual(result.returncode, 3, result.stderr)
        self.assertFalse(self.calls())
        self.assertTrue(all(call == ['-h', 'localhost', '-r']
                            for call in self.stat_calls()))

    def test_inherited_message_locale_does_not_bypass_queue_protection(self):
        env = dict(self.env, LC_MESSAGES='es_ES.UTF-8',
                   QUEUES='printer oficina is idle. enabled since today')
        result = self.run_cli(*self.base(), env=env)
        self.assertEqual(result.returncode, 4, result.stderr)
        self.assertFalse(self.calls())

    def test_queue_listing_failure_stops_before_changes(self):
        env = dict(self.env, LIST_EXIT='1')
        self.assertEqual(self.run_cli(*self.base(), env=env).returncode, 3)
        self.assertFalse(self.calls())

    def test_cups_rejection_is_not_reported_as_success(self):
        env = dict(self.env, ADMIN_EXIT='1')
        result = self.run_cli(*self.base(), env=env)
        self.assertEqual(result.returncode, 5)
        self.assertNotIn('configured and enabled', result.stdout)

    def test_failed_post_install_verification(self):
        env = dict(self.env, VERIFY_EXIT='1')
        self.assertEqual(self.run_cli(*self.base(), env=env).returncode, 5)

    def test_legacy_entry_point(self):
        result = self.run_cli(*self.base(), '--dry-run', script='InstaladorDriberLinux.sh')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.calls())


if __name__ == '__main__':
    unittest.main()
