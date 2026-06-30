import React, { useEffect, useState } from "react";

const MaterialForm = ({
  showForm,
  sensors,
  editingMaterial,
  onSave,
  onClose,
}) => {
  const [name, setName] = useState("");
  const [thresholds, setThresholds] = useState([]);

  useEffect(() => {
    if (editingMaterial) {
      setName(editingMaterial.name);
      setThresholds(editingMaterial.thresholds);
    } else {
      setName("");
      setThresholds(
        sensors.map((s) => ({
          sensor_id: s.id,
          min_value: "",
          max_value: "",
        }))
      );
    }
  }, [editingMaterial, sensors]);

  const handleChange = (index, field, value) => {
    const updated = [...thresholds];
    updated[index][field] = value;
    setThresholds(updated);
  };

  const handleSubmit = () => {
    const cleanedThresholds = thresholds
    .filter(t => t.min_value !== "" && t.max_value !== "")
    .map(t => ({
      sensor_id: t.sensor_id,
      min_value: Number(t.min_value),
      max_value: Number(t.max_value),
    }));


    const payload = {
      name: name,
      active: false,
      thresholds: cleanedThresholds,
    };

    onSave(payload);
  };

  if (!showForm) return null;

  return (
    <div className="bg-slate-800 p-6 rounded-xl space-y-4">
      <h2>{editingMaterial ? "Edit" : "Create"} Material</h2>

      <input
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="Material Name"
        className="w-full p-2 bg-slate-700 rounded"
      />

      {thresholds.map((t, index) => {
        const sensor = sensors.find((s) => s.id === t.sensor_id);

        return (
          <div key={t.sensor_id}>
            <label>{sensor?.name}</label>
            <div className="flex gap-2">
              <input
                placeholder="Min"
                value={t.min_value}
                onChange={(e) =>
                  handleChange(index, "min_value", e.target.value)
                }
                className="w-full p-2 bg-slate-700 rounded"
              />
              <input
                placeholder="Max"
                value={t.max_value}
                onChange={(e) =>
                  handleChange(index, "max_value", e.target.value)
                }
                className="w-full p-2 bg-slate-700 rounded"
              />
            </div>
          </div>
        );
      })}

      <div className="flex justify-end gap-2">
        <button onClick={onClose}>Cancel</button>
        <button
          onClick={handleSubmit}
          className="bg-emerald-600 px-4 py-2 rounded"
        >
          Save
        </button>
      </div>
    </div>
  );
};

export default MaterialForm;