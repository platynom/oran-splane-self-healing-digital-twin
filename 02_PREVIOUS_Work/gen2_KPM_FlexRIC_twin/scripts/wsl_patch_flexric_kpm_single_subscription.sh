#!/usr/bin/env bash
set -euo pipefail

FLEXRIC_DIR="${HOME}/oran-lab/flexric"
SRC="${FLEXRIC_DIR}/examples/xApp/c/monitor/xapp_kpm_moni.c"
BUILD_DIR="${FLEXRIC_DIR}/build-python-xapp"

if [ ! -f "${SRC}" ]; then
  echo "Missing FlexRIC KPM xApp source: ${SRC}"
  exit 1
fi

cp -n "${SRC}" "${SRC}.orig"

python3 - <<'PY'
from pathlib import Path

src = Path.home() / "oran-lab/flexric/examples/xApp/c/monitor/xapp_kpm_moni.c"
text = src.read_text()

old = """    const size_t sz_report_styles = n->rf[idx].defn.kpm.sz_ric_report_style_list;
    hndl[i] = calloc(sz_report_styles, sizeof(sm_ans_xapp_t));
    assert(hndl[i] != NULL);
    for (size_t j = 0; j < sz_report_styles; j++) {
      ric_report_style_item_t *report_item = &n->rf[idx].defn.kpm.ric_report_style_list[j];
      // Generate KPM SUBSCRIPTION message
      kpm_sub_data_t kpm_sub = gen_kpm_subs(&n->rf[idx].defn.kpm, report_item);

      hndl[i][j] = report_sm_xapp_api(&n->id, KPM_ran_function, &kpm_sub, sm_cb_kpm);
      assert(hndl[i][j].success == true);

      free_kpm_sub_data(&kpm_sub);
    }
"""

new = """    const size_t sz_report_styles = n->rf[idx].defn.kpm.sz_ric_report_style_list;
    const size_t active_report_styles = sz_report_styles > 0 ? 1 : 0;
    hndl[i] = calloc(active_report_styles, sizeof(sm_ans_xapp_t));
    assert(hndl[i] != NULL);
    for (size_t j = 0; j < active_report_styles; j++) {
      ric_report_style_item_t *report_item = &n->rf[idx].defn.kpm.ric_report_style_list[j];
      // Local lab stability patch: subscribe to one KPM report style.
      // The emulator can expose multiple styles, but later subscriptions may
      // remain pending and abort the example xApp event loop.
      kpm_sub_data_t kpm_sub = gen_kpm_subs(&n->rf[idx].defn.kpm, report_item);

      hndl[i][j] = report_sm_xapp_api(&n->id, KPM_ran_function, &kpm_sub, sm_cb_kpm);
      assert(hndl[i][j].success == true);

      free_kpm_sub_data(&kpm_sub);
    }
"""

old_cleanup = """    for (size_t j = 0; j < n->rf[idx].defn.kpm.sz_ric_report_style_list; j++) {
      // Remove the handle previously returned
      if (hndl[i][j].success == true)
        rm_report_sm_xapp_api(hndl[i][j].u.handle);
    }
"""

new_cleanup = """    const size_t sz_report_styles = n->rf[idx].defn.kpm.sz_ric_report_style_list;
    const size_t active_report_styles = sz_report_styles > 0 ? 1 : 0;
    for (size_t j = 0; j < active_report_styles; j++) {
      // Remove the handle previously returned
      if (hndl[i][j].success == true)
        rm_report_sm_xapp_api(hndl[i][j].u.handle);
    }
"""

if old not in text:
    raise SystemExit("Could not find subscription block to patch; source may have changed.")
text = text.replace(old, new)
if old_cleanup not in text:
    raise SystemExit("Could not find cleanup block to patch; source may have changed.")
text = text.replace(old_cleanup, new_cleanup)
src.write_text(text)
print(f"Patched {src}")
PY

cmake --build "${BUILD_DIR}" --target xapp_kpm_moni -j1

echo "Patched KPM monitor rebuilt:"
echo "${BUILD_DIR}/examples/xApp/c/monitor/xapp_kpm_moni"
