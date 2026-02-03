from src.pipeline.stage_runtime import make_manifest


def run(config):
    out = config.analytics_dir / 'export_manifest.txt'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text('Export stage placeholder\n', encoding='utf-8')
    return make_manifest([], [out], 0, 0)
