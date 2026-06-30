import React from "react";

const MaterialCard = ({ material, sensors, onEdit, onToggle, handleDelete }) => {
  return (
    <div className="bg-slate-800 p-4 rounded flex justify-between">
      <div>
        <h3 className="font-bold">{material.name}</h3>

        <p className="text-sm text-gray-400">
          {material.thresholds.map((t) => {
            const sensor = sensors.find((s) => s.id === t.sensor_id);
            return `${sensor?.name}: ${t.min_value}-${t.max_value}`;
          }).join(" | ")}
        </p>

        <p className={material.active ? "text-green-400" : "text-red-400"}>
          {material.active ? "Active" : "Inactive"}
        </p>
      </div>

      <div className="flex gap-2">
        <button onClick={onEdit} className="bg-blue-600 px-2 py-1 rounded">
          Edit
        </button>

        <button
          onClick={onToggle}
          className="bg-yellow-600 px-2 py-1 rounded"
        >
          Toggle
        </button>

        <button
            onClick={() => handleDelete(material)}
            className="px-3 py-1 bg-red-600 rounded"
        >
            Delete
        </button>
      </div>
    </div>
  );
};

export default MaterialCard;