import React, { useState, useEffect } from "react";
import SensorCard from "./sensorCard";
import { SensorModal } from "./sensorModel";
import { useMutation } from "@tanstack/react-query";
import safeApi from "../../../api/safeApi";
import { useTranslation } from "react-i18next";
import { useErrorToast } from "../../subComponents/errorToast";

const Sensors = () => {
  const { t } = useTranslation();

  const { showError, ErrorComponent } = useErrorToast();

  const [selectedMachine, setSelectedMachine] = useState("");
  const [sensors, setSensors] = useState([]);
  const [allMachines, setAllMachines] = useState([]);
  const [showCreateModal, setShowCreateModal] = useState(false);

  const [loading, setLoading] = useState(true);
  const [isEditing,setIsEditing] = useState(false);
    const [selectedSensor,setSelectedSensor] =useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  async function fetchData() {
    try {
      setLoading(true);

      const [sensorRes, machineRes] = await Promise.all([
        safeApi.get("/default-sensors"),
        safeApi.get("/machines"),
      ]);

      setSensors(sensorRes.data || []);
      setAllMachines(machineRes.data || []);
    } catch (err) {
      showError("Failed to load sensors");
    } finally {
      setLoading(false);
    }
  }

// CREATE
const createMutation = useMutation({
  mutationFn: (data) =>
    safeApi.post("/default-sensors", data),

  onSuccess: (res) => {
    setSensors((prev) => [...prev, res.data]);

    setShowCreateModal(false);
  },

  onError: () => {
    showError("Unable to create sensor");
  },
});


// UPDATE
const updateMutation = useMutation({
    mutationFn: ({ id, data }) =>
        safeApi.put(
        `/default-sensors/${id}`,
        data
        ),

    onSuccess: (res, variables) => {

        setSensors((prev) =>
        prev.map((s) =>
            s.id === variables.id
            ? res.data
            : s
        )
        );

        setIsEditing(false);
        setSelectedSensor(null);
    },

    onError: () => {
        showError(
        "Unable to update sensor"
        );
    },
    });


    // DELETE
    const deleteMutation = useMutation({
    mutationFn: (id) =>
        safeApi.delete(
        `/default-sensors/${id}`
        ),

    onSuccess: (_, id) => {
        setSensors((prev) =>
        prev.filter(
            (s) => s.id !== id
        )
        );
    },

    onError: () => {
        showError(
        "Unable to delete sensor"
        );
    },
    });

  const filteredSensors =
    selectedMachine === ""
      ? sensors
      : sensors.filter(
          (s) => s.machine_id === selectedMachine
        );

  return (
    <div className="space-y-6">

      <div className="flex justify-between items-center">

        <div>
          <h1 className="text-3xl font-bold text-[#a551f4]">
            {t("sensors")}
          </h1>

          <p className="text-slate-400">
            Manage Default Sensors
          </p>
        </div>

        <div className="flex gap-3">

          <select
            value={selectedMachine}
            onChange={(e) =>
              setSelectedMachine(e.target.value)
            }
            className="
            px-4 py-2
            bg-slate-900
            border border-slate-700
            rounded-xl
            text-white"
          >
            <option value="">
              All Machines
            </option>

            {allMachines.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name}
              </option>
            ))}
          </select>

          <button
            onClick={() =>
              setShowCreateModal(true)
            }
            className="
            px-5 py-2
            rounded-xl
            bg-emerald-600
            hover:bg-emerald-500"
          >
            + Add Sensor
          </button>

        </div>

      </div>

      {loading && (
        <div className="text-center py-12 text-slate-400">
          Loading sensors...
        </div>
      )}

      {!loading &&
        filteredSensors.length === 0 && (
          <div className="text-center py-12 text-slate-400">
            No sensors found
          </div>
        )}

      <div className="grid gap-4">

        {filteredSensors.map((sensor) => (
            <SensorCard
                key={sensor.id}
                sensor={sensor}
                deleteMutation={deleteMutation}
                setSelectedSensor={setSelectedSensor}
                setIsEditing={setIsEditing}
            />
        ))}

      </div>

      <SensorModal
            isOpen={showCreateModal || isEditing}
            onClose={()=>{
                setShowCreateModal(false)
                setIsEditing(false)
                setSelectedSensor(null)
            }}

            sensor={selectedSensor}
            isEditing={isEditing}
            machines={allMachines}
            onSave={(data)=>{
                if(
                isEditing &&
                selectedSensor
                ){
                updateMutation.mutate({
                    id:selectedSensor.id,
                    data
                })
                }else{
                createMutation.mutate(data)
                }
            }}
            isLoading={
                createMutation.isPending ||
                updateMutation.isPending
            }
      />

      {ErrorComponent}
    </div>
  );
};

export default Sensors;