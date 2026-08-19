// sceneseek-frontend/src/utils/clusterGrouping.js

/**
 * Group a flat list of clusters/events (from event-boundary or event-mention)
 * by video_id, preserving first-seen order. Each group can have 1+ events
 * (event-boundary usually has 1 per video per page; event-mention can have many,
 * e.g. multiple transcript matches within the same video).
 *
 * NOTE: grouping only happens within the CURRENT PAGE's results — pagination
 * is done backend-side on the flat cluster list, so if 2 events of the same
 * video land on different pages, they'll render as 2 separate groups.
 */
export function groupClustersByVideo(clusters) {
  const order = [];
  const map = new Map();
  for (const c of clusters) {
    if (!map.has(c.video_id)) {
      map.set(c.video_id, []);
      order.push(c.video_id);
    }
    map.get(c.video_id).push(c);
  }
  return order.map((video_id) => ({ video_id, events: map.get(video_id) }));
}