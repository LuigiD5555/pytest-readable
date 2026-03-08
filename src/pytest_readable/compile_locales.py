"""PO to MO compiler copied inline for offline localization maintenance."""

import ast
import struct
from pathlib import Path


LOCALE_DIR = Path(__file__).with_name("locale")
MAGIC = 0x950412DE


def _unquote_po_string(token: str) -> str:
    """Decode the literal string used inside a PO file entry."""
    return ast.literal_eval(token)


def _parse_po(path: Path) -> dict[str, str]:
    """Read a PO file and return a mapping from msgid to msgstr."""
    catalog: dict[str, str] = {}
    msgid: str | None = None
    msgstr: str | None = None
    current: str | None = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("msgid "):
            if msgid is not None and msgstr is not None:
                catalog[msgid] = msgstr
            msgid = _unquote_po_string(line[6:])
            msgstr = None
            current = "msgid"
            continue

        if line.startswith("msgstr "):
            msgstr = _unquote_po_string(line[7:])
            current = "msgstr"
            continue

        if line.startswith('"'):
            value = _unquote_po_string(line)
            if current == "msgid" and msgid is not None:
                msgid += value
            elif current == "msgstr" and msgstr is not None:
                msgstr += value
            continue

        raise ValueError(f"Unsupported .po syntax in {path}: {raw_line}")

    if msgid is not None and msgstr is not None:
        catalog[msgid] = msgstr

    return catalog


def _compile_catalog(messages: dict[str, str]) -> bytes:
    """Emit the binary MO catalog format from decoded message pairs."""
    items = sorted(messages.items())

    ids = b""
    strs = b""
    id_offsets: list[tuple[int, int]] = []
    str_offsets: list[tuple[int, int]] = []

    for msgid, msgstr in items:
        msgid_bytes = msgid.encode("utf-8")
        msgstr_bytes = msgstr.encode("utf-8")

        id_offsets.append((len(msgid_bytes), len(ids)))
        str_offsets.append((len(msgstr_bytes), len(strs)))

        ids += msgid_bytes + b"\0"
        strs += msgstr_bytes + b"\0"

    count = len(items)
    header_size = 7 * 4
    key_index_offset = header_size
    value_index_offset = key_index_offset + count * 8
    ids_offset = value_index_offset + count * 8
    strs_offset = ids_offset + len(ids)

    output = bytearray()
    output.extend(
        struct.pack(
            "Iiiiiii",
            MAGIC,
            0,
            count,
            key_index_offset,
            value_index_offset,
            0,
            0,
        )
    )

    for length, offset in id_offsets:
        output.extend(struct.pack("II", length, ids_offset + offset))

    for length, offset in str_offsets:
        output.extend(struct.pack("II", length, strs_offset + offset))

    output.extend(ids)
    output.extend(strs)
    return bytes(output)


def compile_po_file(po_path: Path) -> Path:
    """Compile a single `.po` file to a `.mo` binary catalog."""
    mo_path = po_path.with_suffix(".mo")
    catalog = _parse_po(po_path)
    mo_path.write_bytes(_compile_catalog(catalog))
    return mo_path


def compile_all_locales(locale_dir: Path = LOCALE_DIR) -> list[Path]:
    """Compile every `.po` found under the locale directory."""
    compiled = []
    for po_path in sorted(locale_dir.rglob("*.po")):
        compiled.append(compile_po_file(po_path))
    return compiled


def main() -> None:
    """Console helper that rebuilds every MO catalog when called."""
    compiled = compile_all_locales()
    for path in compiled:
        print(path)


if __name__ == "__main__":
    main()
