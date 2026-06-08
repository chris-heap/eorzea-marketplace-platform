import { useState } from "react";
import { getPrices } from "../api/client";

function PriceSearch() {
  const [search, setSearch] = useState("");
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searched, setSearched] = useState(false);

  async function handleSearch(e) {
    e.preventDefault();
    if (!search.trim()) return;

    setLoading(true);
    setError(null);
    setSearched(true);

    try {
      const rows = await getPrices(search);
      setData(rows);
    } catch (err) {
      setError(err.message);
      setData([]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="panel">
      <form className="panel-controls" onSubmit={handleSearch}>
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search for an item... (e.g. Iron Ore, Tsai tou Vounou)"
        />
        <button type="submit" disabled={loading}>
          Search
        </button>
      </form>

      {loading && <div className="spinner">Searching the market board...</div>}
      {error && <p className="status error">{error}</p>}

      {!loading && searched && data.length === 0 && !error && (
        <p className="status">No retainers are selling that item right now.</p>
      )}

      {data.length > 0 && (
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Item</th>
                <th>World</th>
                <th>HQ</th>
                <th>Listings</th>
                <th>Avg Price</th>
                <th>Min</th>
                <th>Max</th>
              </tr>
            </thead>
            <tbody>
              {data.map((row, i) => (
                <tr key={i}>
                  <td>{row.item_name}</td>
                  <td>{row.world_name}</td>
                  <td>{row.is_hq ? "★ HQ" : "NQ"}</td>
                  <td>{row.listing_count}</td>
                  <td>{Number(row.avg_price).toLocaleString()} gil</td>
                  <td>{Number(row.min_price).toLocaleString()} gil</td>
                  <td>{Number(row.max_price).toLocaleString()} gil</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default PriceSearch;
