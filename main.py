structure = {
    "00_发刊词": [
        "0.1_任何市场环境_你都能有机会"
    ],
    "01_模块一_什么是行为金融学": [
        "1.1_行为金融学为何擅长投资实战",
        "1.2_人是不是真的有智慧战胜市场",
        "1.3_价格错误是如何产生的",
        "1.4_现实生活中_你应该如何套利"
    ],
    "02_模块二_认知非理性": [
        "2.1_你能真正了解一家公司吗_信息收集阶段的认知偏差",
        "2.2_为什么股评不可信_信息加工阶段的认知偏差",
        "2.3_为什么人越自信赔得越多_信息输出阶段的认知偏差",
        "2.4_踩过的坑为什么还会踩_信息反馈阶段的认知偏差",
        "2.5_盈利和亏损得看参考点_参考点依赖"
    ],
    "03_模块三_决策非理性": [
        "3.1_牛市赚不到头_熊市一亏到底_盈利和亏损的不同风险偏好",
        "3.2_为何投资者总把小概率事件扩大化_错判概率导致的决策偏差",
        "3.3_为何不能天天查看自选股_狭隘框架",
        "3.4_做股票亏了无所谓而吃饭钱丢了可不行_心理账户理论",
        "3.5_股票市场就是个选美博弈_我得看你怎么选"
    ],
    "04_模块四_典型的交易错误": [
        "4.1_买熟悉的股票不对吗_分散化不足",
        "4.2_为什么把鸡蛋放在不同篮子里还是赔了_简单分散化",
        "4.3_来回倒腾为什么不如不动_过度交易理论",
        "4.4_卖出盈利的还是亏损的_卖出行为偏差",
        "4.5_涨停敢死队怎么赚钱的_买入行为偏差",
        "4.6_追逐热点投资对不对_羊群效应"
    ],
    "05_模块五_股票大盘的奥秘": [
        "5.1_大盘可以预测吗_大盘可预测理论",
        "5.2_无论如何你都应该买点股票_股权溢价之谜和战略资产配置",
        "5.3_怎样解读放量_价量关系理论1_Miller假说",
        "5.4_你参与了股票市场的击鼓传花_价量关系理论2_博傻理论"
    ],
    "06_模块六_行为投资策略": [
        "6.1_行为金融交易策略如何盈利_利用人们的错误",
        "6.2_为何会有免费的午餐_行为组合策略原理",
        "6.3_买大公司还是小公司的股票_规模溢价和价值溢价",
        "6.4_跌久必涨还是惯性效应_如何用好股价规律",
        "6.5_财报里藏了什么秘密_利用财务报表信息来制定交易策略",
        "6.6_免费的午餐一直都有_持续获得有效的投资策略"
    ],
    "07_模块七_实战分析": [
        "7.1_实战_贵州茅台的股票值得持有吗",
        "7.2_实战_从乐视网看公司基本面",
        "7.3_实战_股市大跌时如何应对",
        "7.4_实战_大盘短期能否预测",
        "7.5_实战_如何对待股权质押类资产",
        "7.6_实战_概念股炒作中_投资者怎么做",
        "7.7_实战_如何应对股市中的黑天鹅事件"
    ]
}



import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from zipfile import ZIP_DEFLATED, ZipFile


def expected_lessons():
    """Return stable relative Markdown paths from the existing course catalog."""
    for section, titles in structure.items():
        for index, title in enumerate(titles):
            safe_title = title.replace(' ', '_').replace('/', '_').replace('-', '_')
            yield Path(section) / f'{index:02d}_{safe_title}.md'


def initialize(root: Path, *, dry_run: bool = False) -> dict:
    """Create only missing lesson skeletons, never modify existing files."""
    created, existing = [], []
    for relative in expected_lessons():
        target = root / relative
        if target.exists() or target.is_symlink():
            existing.append(relative.as_posix())
            continue
        if not dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            try:
                with target.open('x', encoding='utf-8') as stream:
                    stream.write(f'# {target.stem}\n\n')
                    stream.write(f'<!-- TODO: lesson source {relative.as_posix()} -->\n')
            except FileExistsError:
                existing.append(relative.as_posix())
                continue
        created.append(relative.as_posix())
    return {'created': created, 'existing': existing, 'dry_run': dry_run}


def audit(root: Path) -> dict:
    """Read-only inventory differentiating notes from generated skeletons."""
    missing, placeholders, substantive = [], [], []
    for relative in expected_lessons():
        target = root / relative
        name = relative.as_posix()
        if not target.is_file():
            missing.append(name)
            continue
        body = target.read_text(encoding='utf-8')
        if '"""' in body:
            body = body.rsplit('"""', 1)[-1]
        if len(body.strip()) < 80 or '<!-- TODO:' in body:
            placeholders.append(name)
        else:
            substantive.append(name)
    return {'expected': len(missing) + len(placeholders) + len(substantive),
            'substantive': len(substantive), 'placeholders': placeholders,
            'missing': missing}


def content_files(root: Path):
    """Legacy course documents and site assets only; never follow symlinks."""
    extensions = {'.md', '.html', '.pdf', '.css', '.js'}
    for child in sorted(root.iterdir()):
        if child.is_symlink():
            raise ValueError(f'Symlinks are not backed up: {child}')
        if child.is_file() and (child.suffix in extensions or child.name == 'main.py'):
            yield child
        if child.is_dir() and child.name[:2].isdigit() and child.name[2:3] == '_':
            for file in sorted(child.rglob('*')):
                if file.is_symlink():
                    raise ValueError(f'Symlinks are not backed up: {file}')
                if file.is_file() and file.suffix in extensions:
                    yield file


def backup(root: Path, archive: Path) -> dict:
    """Create an exclusive ZIP with per-file SHA-256 hashes; never overwrite."""
    files = list(content_files(root))
    if not files:
        raise ValueError('No course files found; refusing an empty backup')
    archive.parent.mkdir(parents=True, exist_ok=True)
    records = []
    with ZipFile(archive, mode='x', compression=ZIP_DEFLATED) as output:
        for source in files:
            relative = source.relative_to(root).as_posix()
            contents = source.read_bytes()
            records.append({'path': relative, 'sha256': hashlib.sha256(contents).hexdigest(),
                            'bytes': len(contents)})
            output.writestr(relative, contents)
        manifest = {'schema_version': 1,
                    'created_at_utc': datetime.now(timezone.utc).isoformat(),
                    'files': records}
        output.writestr('backup-manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2))
    return {'archive': str(archive), 'files': len(records),
            'verified': verify_backup(archive)['valid']}


def verify_backup(archive: Path) -> dict:
    """Validate a backup without extracting or trusting archive entry paths."""
    with ZipFile(archive, 'r') as source:
        entries = source.namelist()
        if len(entries) != len(set(entries)) or entries.count('backup-manifest.json') != 1:
            raise ValueError('Duplicate or missing manifest entries')
        manifest = json.loads(source.read('backup-manifest.json'))
        if manifest.get('schema_version') != 1 or not isinstance(manifest.get('files'), list):
            raise ValueError('Unsupported backup manifest')
        paths = []
        for record in manifest['files']:
            path = record['path']
            parts = PurePosixPath(path).parts
            if not parts or path.startswith('/') or any(p in ('.', '..') for p in parts):
                raise ValueError(f'Unsafe backup path: {path}')
            data = source.read(path)
            if (len(data) != record['bytes'] or
                    hashlib.sha256(data).hexdigest() != record['sha256']):
                raise ValueError(f'Backup integrity check failed: {path}')
            paths.append(path)
        if len(paths) != len(set(paths)) or set(entries) != set(paths) | {'backup-manifest.json'}:
            raise ValueError('Archive and manifest do not match')
    return {'valid': True, 'files': len(paths)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Safe course content tools')
    parser.add_argument('command', nargs='?', default='audit',
                        choices=['audit', 'init', 'backup', 'verify-backup'])
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--archive', type=Path, help='Required for backup/verify-backup')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--strict', action='store_true',
                        help='Fail audit on missing/placeholder lessons')
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if args.command == 'audit':
        result = audit(root)
        exit_code = int(args.strict and bool(result['missing'] or result['placeholders']))
    elif args.command == 'init':
        result, exit_code = initialize(root, dry_run=args.dry_run), 0
    else:
        if args.archive is None:
            parser.error('--archive is required for backup and verify-backup')
        result = (backup(root, args.archive) if args.command == 'backup'
                  else verify_backup(args.archive))
        exit_code = 0
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return exit_code


if __name__ == '__main__':
    raise SystemExit(main())
