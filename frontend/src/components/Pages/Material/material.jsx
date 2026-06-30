import React, { useEffect, useState } from "react";
import MaterialCard from "./materialCard";
import MaterialForm from "./materialForm";
// import { useBackendStore } from "../../../store/backendStore";
import safeApi from "../../../api/safeApi";

const MaterialProfiles = ({backendStatus}) => {
  // const backendStatus = useBackendStore((state) => state.status);

  const [materials, setMaterials] = useState([]);
  const [toggle, setToggle] = useState(false)
  const [sensors, setSensors] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editingMaterial, setEditingMaterial] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [sensorRes, materialRes] = await Promise.all([
          safeApi.get("/default-sensors"),
          safeApi.get("/material-profiles"),
        ]);

        setSensors((prev) => sensorRes?.data || prev);
        setMaterials((prev) => materialRes?.data || prev);
      } catch (err) {
        console.error(err);
      }
    };

    fetchData();
  }, [backendStatus, toggle]);

  // CREATE / UPDATE
  const handleSave = async (payload) => {
    try {
      if (editingMaterial) {
        const res = await safeApi.put(
          `/material-profiles/${editingMaterial.id}`,
          payload
        );
        setMaterials((prev) =>
          prev.map((m) => (m.id === editingMaterial.id ? res.data : m))
        );
      } else {
        console.log(payload)
        const res = await safeApi.post("/material-profiles", payload);
        setMaterials((prev) => [...prev, res.data]);
      }

      setShowForm(false);
      setEditingMaterial(null);
    } catch (err) {
      console.error("Save error:", err);
    }
  };

  // TOGGLE ACTIVE
  const toggleActive = async (material) => {
    try {
      const res = await safeApi.patch(
        `/material-profiles/${material.id}/toggle`
      );

      setMaterials((prev) =>
        prev.map((m) => (m.id === material.id ? res.data : m))
      );
    } catch (err) {
      console.error(err);
    }

    finally{
      setToggle((prev) => prev===false?true:false);
    }
  };

  const handleDelete = async (material) => {
    if (!window.confirm(`Are you sure you want to delete "${material.name}"?`)) return;

    try {
      await safeApi.delete(`/material-profiles/${material.id}`);

      // Remove from local state
      setMaterials(prev => prev.filter(m => m.id !== material.id));
    } catch (err) {
      console.error("Delete error:", err);
      alert("Failed to delete material profile");
    }
  };
  return (
    <div className="p-6 text-white">
      <div className="flex justify-between mb-4">
        <h1 className="text-2xl font-bold text-purple-400">
          Material Profiles
        </h1>

        <button
          onClick={() => {
            setEditingMaterial(null);
            setShowForm(true);
          }}
          className="bg-emerald-600 px-4 py-2 rounded"
        >
          + Create
        </button>
      </div>

      <MaterialForm
        showForm={showForm}
        sensors={sensors}
        editingMaterial={editingMaterial}
        onSave={handleSave}
        onClose={() => setShowForm(false)}
      />

      <div className="space-y-3 mt-4">
        {materials.map((m) => (
          <MaterialCard
            key={m?.id}
            material={m}
            sensors={sensors}
            onEdit={() => {
              setEditingMaterial(m);
              setShowForm(true);
            }}
            handleDelete={handleDelete}
            onToggle={() => toggleActive(m)}
          />
        ))}
      </div>
    </div>
  );
};

export default MaterialProfiles;