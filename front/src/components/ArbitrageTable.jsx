import { useState, useEffect } from "react";
import { getArbitrage } from "../api/client";

function ArbitrageTable() {
  const [data, setData] = useState([]);
  const [minMargin, setMinMargin] = useState(50);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  async function fetchData() {
    setLoading(true);
    setError(null);
    try {
      const rows = await getArbitrage(minMargin);
      setData(rows);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="panel">
      <div className="panel-controls">
        <label>
          Min margin %
          <input
            type="number"
            value={minMargin}
            onChange={(e) => setMinMargin(Number(e.target.value))}
          />
        </label>
        <button onClick={fetchData}>Refresh</button>
      </div>

      {loading && <div className="spinner">Loading arbitrage opportunities...</div>}
      {error && <p className="status error">{error}</p>}

      {!loading && !error && (
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Item</th>
                <th>World</th>
                <th>HQ</th>
                <th>Price</th>
                <th>Cheapest</th>
                <th>Priciest</th>
                <th>Margin</th>
              </tr>
            </thead>
            <tbody>
              {data.map((row, i) => (
                <tr key={i}>
                  <td>{row.item_name}</td>
                  <td>{row.world_name}</td>
                  <td>{row.is_hq ? "★ HQ" : "NQ"}</td>
                  <td>{Number(row.min_price).toLocaleString()} gil</td>
                  <td>{Number(row.cheapest_price).toLocaleString()} gil</td>
                  <td>{Number(row.priciest_price).toLocaleString()} gil</td>
                  <td className="highlight">
                    {Number(row.profit_margin_pct).toFixed(1)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default ArbitrageTable;
