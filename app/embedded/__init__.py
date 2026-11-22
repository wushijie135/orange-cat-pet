from . import parts

MANIFEST = {'idle': 8, 'blink': 7, 'talk': 8, 'happy': 29, 'sleep': 28}

ASSETS_B64 = {}
for _name, _count in MANIFEST.items():
    _chunks = []
    for _i in range(_count):
        _mod = __import__(f"app.embedded.parts.{_name}_{_i}", fromlist=["P"])
        _chunks.append(_mod.P)
    ASSETS_B64[_name] = "".join(_chunks)
