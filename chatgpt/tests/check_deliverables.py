"""Check delivered files, scientific freeze and preservation; no visual QA claim."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
checks = []


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(name, passed, detail=None):
    checks.append(dict(check=name, passed=bool(passed), detail=detail))


def read(name):
    return json.loads((ROOT / name).read_text())


freeze = read('sources/independent_freeze.json')['files']
changed = [p for p, digest in freeze.items() if sha(ROOT / p) != digest]
check('independent_analysis_unchanged_since_freeze', not changed,
      {'file_count': len(freeze), 'changed': changed})
prior = read('sources/prior_project_manifest.json')
original = ROOT.parent / 'asa_dataquest'
if original.exists():
    metadata_changed = [p for p, digest in prior.items() if p.endswith('.DS_Store') and sha(original / p) != digest]
    changed = [p for p, digest in prior.items() if not p.endswith('.DS_Store') and sha(original / p) != digest]
    check('original_project_files_unchanged', not changed,
          {'file_count': len(prior), 'changed': changed, 'excluded_Finder_metadata_changes': metadata_changed})
    status = subprocess.check_output(['git', '-C', str(original), 'status', '--porcelain'], text=True)
    check('original_git_checkout_clean', not status.strip(), status)

check('raw_source_hashes_match', all(sha(ROOT / 'data/raw' / x['file']) == x['sha256']
                                   for x in read('sources/input_manifest.json')))
check('fresh_dropbox_download_matches', all(x['identical'] for x in read('sources/dropbox_verification.json')))
validation = read('results/validation.json')
check('main_analysis_checks', all(x['passed'] for x in validation), len(validation))
check('second_implementation_passes', read('results/independent_verification.json')['passed'])
comparison = read('results/comparison_summary.json')
check('legacy_tables_reproduced', all(x['identical_bytes'] for x in comparison['rerun_legacy_tables']),
      len(comparison['rerun_legacy_tables']))

pptx = ROOT / 'slides/ASA2026_Demographic_Momentum.pptx'
receipt = read('results/presentation_validation.json')
check('pptx_matches_finalizer_receipt', sha(pptx) == receipt['finalSha256'])
check('presentation_package_integrity', receipt['packageIntegrity']['findingCount'] == 0)
check('presentation_layout_geometry', receipt['presentationLayout']['findingCount'] == 0)
ns = {'c': 'http://schemas.openxmlformats.org/drawingml/2006/chart'}
with zipfile.ZipFile(pptx) as z:
    names = z.namelist()
    count = lambda pattern: sum(bool(re.fullmatch(pattern, name)) for name in names)
    check('six_slides_cover_four_content_references', count(r'ppt/slides/slide\d+\.xml') == 6)
    check('six_speaker_notes', count(r'ppt/notesSlides/notesSlide\d+\.xml') == 6)
    charts = [n for n in names if '/charts/' in n and n.endswith('.xml') and '/_rels/' not in n]
    check('four_editable_native_charts', len(charts) == 4, len(charts))
    workbooks = [n for n in names if n.endswith('.xlsx')]
    check('four_embedded_chart_workbooks', len(workbooks) == 4, len(workbooks))
    scatter = ET.fromstring(z.read('ppt/slides/charts/chart1.xml'))
    series = scatter.findall('.//c:ser', ns)
    data = read('slides/chart_data.json')['scatter']
    x = [float(v.text) for v in series[0].findall('c:xVal/c:numRef/c:numCache/c:pt/c:v', ns)]
    y = [float(v.text) for v in series[0].findall('c:yVal/c:numRef/c:numCache/c:pt/c:v', ns)]
    check('scatter_contains_exactly_237_real_observations', len(series) == 1 and len(x) == len(y) == 237)
    check('scatter_matches_analysis', x == [round(v['TFR'], 8) for v in data]
          and y == [round(v['total_change_pct_base'], 8) for v in data])

pdf_info = subprocess.check_output(['pdfinfo', str(pptx.with_suffix('.pdf'))], text=True)
check('pdf_has_six_pages', bool(re.search(r'Pages:\s+6\b', pdf_info)))
video = ROOT / 'slides/rehearsal.mp4'
probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_format', '-show_streams',
                                          '-of', 'json', str(video)], text=True))
duration = float(probe['format']['duration'])
check('rehearsal_under_five_minutes', 0 < duration < 300, duration)
check('rehearsal_has_audio_and_video', {s['codec_type'] for s in probe['streams']} >= {'audio', 'video'})
timing = read('slides/video_timing.json')
check('synthetic_rehearsal_disclosed', timing['synthetic_voice'] and not timing['submitted'])
for f in ('reports/RAPOR_TR.md', 'reports/DENETIM.md', 'reports/KAYNAKLAR.md',
          'reports/TESLIM_KONTROL.md', 'slides/VIDEO_SCRIPT_EN.md', 'slides/VIDEO_SCRIPT_TR.md'):
    check('document_exists_' + f, (ROOT / f).stat().st_size > 100)

result = {'passed': all(c['passed'] for c in checks), 'checks': checks,
          'scope': 'File integrity and numeric/structural checks. Separate visual review used Artifact Tool and LibreOffice. Native PowerPoint was not run.'}
(ROOT / 'results/deliverable_validation.json').write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
assert result['passed'], 'See failed checks above'
