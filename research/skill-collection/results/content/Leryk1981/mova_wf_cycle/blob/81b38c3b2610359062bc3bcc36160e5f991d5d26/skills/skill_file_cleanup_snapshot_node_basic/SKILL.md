# skill.file_cleanup_snapshot_node_basic

Baseline snapshot skill for file_cleanup.
- Input: `env.file_cleanup_snapshot_request_v1`
- Output: `ds.file_cleanup_snapshot_v1`
- Action: recursively scan `target.root_path`, collect file/folder metadata and stats. No deletions or file mutations.
