import { useState, useEffect } from "react";
import { getVelocity } from "../api/client";

function VelocityTable() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  async function fetchData() {
    setLoading(true);
    setError(null);
    try {
      const rows = await getVelocity();
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
        <button onClick={fetchData}>Refresh</button>
      </div>

      {loading && <div className="spinner">Loading top sellers...</div>}
      {error && <p className="status error">{error}</p>}

      {!loading && !error && (
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Item</th>
                <th>World</th>
                <th>Date</th>
                <th>Sales</th>
                <th>Volume</th>
                <th>Avg Price</th>
              </tr>
            </thead>
            <tbody>
              {data.map((row, i) => (
                <tr key={i}>
                  <td>{row.item_name}</td>
                  <td>{row.world_name}</td>
                  <td>{row.sale_date}</td>
                  <td className="highlight">{row.sale_count}</td>
                  <td>{Number(row.total_volume).toLocaleString()} gil</td>
                  <td>{Number(row.avg_price).toLocaleString()} gil</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default VelocityTable;
