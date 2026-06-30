import { useState,useEffect } from "react";
import toast from "react-hot-toast";
import { useTranslation } from "react-i18next";

const BaselineModal = ({
    isOpen,
    onClose,
    onSave,
    machineStates,
    sensors,
    isLoading,
    isEditing,
    baseline
}) => {
    const [name, setName] = useState("");
    const { t } = useTranslation();
    const [stateData, setStateData] = useState({});

    // INITIALIZE WHEN EDITING
    useEffect(() => {
        if (baseline && isEditing) {
            setName(baseline.baseline_name || "");

            const formatted = {};

            (baseline.mappings || []).forEach((state) => {
                formatted[state.machine_state_id] = {
                    mappings: (state.mappings || []).map((m) => ({
                        sensor_id: m.sensor_id,
                        min_value: m.min_value,
                        max_value: m.max_value
                    }))
                };
            });

            setStateData(formatted);
        } else {
            setName("");
            setStateData({});
        }
    }, [baseline, isEditing]);

    if (!isOpen) return null;



    const handleAddSensor = (stateId) => {
        setStateData((prev) => ({
            ...prev,
            [stateId]: {
                mappings: [
                    ...(prev[stateId]?.mappings || []),
                    { sensor_id: "", min_value: "", max_value: "" }
                ]
            }
        }));
    };

    const handleChange = (stateId, index, field, value) => {
        const updated = [...(stateData[stateId]?.mappings || [])];
        updated[index][field] = value;

        setStateData((prev) => ({
            ...prev,
            [stateId]: {
                mappings: updated
            }
        }));
    };

    const validateStateData = () => {
        if (!stateData || Object.keys(stateData).length === 0) {
            return
        }
        
    }

    const handleSubmit = () => {
        if(!name){
            toast.error(t("messages.name_required"));   
            return
        }


        if (!stateData || Object.keys(stateData).length === 0) {
            toast.error(t("messages.sensor_required"));
            return false;
        }

        // ✅ NEW VALIDATION BLOCK
        for (const [stateId, sensors] of Object.entries(stateData)) {
            if (!sensors?.mappings || sensors.mappings.length === 0) {
                toast.error(`State ${stateId} has no sensors.`);
                return;
            }

            for (const s of sensors.mappings) {
                if (
                    Number(s.sensor_id) === 0 ||
                    s.min_value === null || s.min_value === "" || isNaN(Number(s.min_value)) ||
                    s.max_value === null || s.max_value === "" || isNaN(Number(s.max_value))
                ) {
                    toast.error(t("messages.sensor_invalid"));
                    return;
                }
            }    
        }
        
        const payload = {
            
            baseline_name: name,  // ✅ FIXED (was name before)
            mappings: Object.entries(stateData).map(
                ([stateId, sensors]) => ({
                    
                    
                    machine_state_id: Number(stateId),

                    mappings: sensors['mappings'].map((s) => ({
                        sensor_id: Number(s.sensor_id),
                        min_value: s.min_value !== null && s.min_value !== undefined ? Number(s.min_value) : null,
                        max_value: s.max_value !== null && s.max_value !== undefined ? Number(s.max_value) : null
                    }))
                })
            )
        };
        console.log(payload);
        onSave(payload);
    };

    
    return (
        <div className="fixed inset-0 bg-black/50 flex justify-center items-center z-50">
            <div className="bg-slate-900 p-6 rounded-xl w-[900px] max-h-[90vh] overflow-y-auto">

                <h2 className="text-xl font-bold mb-4 text-white">{isEditing? t("baseline.edit") : t("baseline.create")}</h2>

                {/* Baseline Name */}
                <input
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder={t("baseline.name_placeholder")}
                    className="w-full mb-4 p-2 rounded bg-slate-800 text-white"
                />

                {/* Machine States */}
                {machineStates.map((state) => (
                    <div key={state.id} className="mb-6 border p-3 rounded">

                        <div className="flex justify-between">
                            <h3 className="font-semibold text-white">{state.name}</h3>

                            <button
                                onClick={() => handleAddSensor(state.id)}
                                className="text-sm bg-blue-600 px-2 py-1 rounded text-white"
                            >
                                + {t("baseline.add_sensor")}
                            </button>
                        </div>

                        {(stateData[state.id]?.mappings || []).map((sensorRow, i) => (
                            <div key={i} className="flex gap-2 mt-2">

                                {/* Sensor Dropdown */}
                                <select
                                    value={sensorRow.sensor_id || ""}
                                    onChange={(e) =>
                                        handleChange(state.id, i, "sensor_id", e.target.value)
                                    }
                                    className="bg-slate-800 p-2 rounded text-white"
                                >
                                    <option value="">{t("baseline.select_sensor")}</option>
                                    {sensors.map((s) => (
                                        <option key={s.id} value={s.id}>
                                            {s.name}
                                        </option>
                                    ))}
                                </select>

                                {/* Min */}
                                <input
                                    type="number"
                                    placeholder={t("baseline.min")}
                                    value={sensorRow.min_value}
                                    onChange={(e) =>
                                        handleChange(state.id, i, "min_value", e.target.value)
                                    }
                                    className="bg-slate-800 p-2 rounded w-24 text-white"
                                />

                                {/* Max */}
                                <input
                                    type="number"
                                    placeholder={t("baseline.max")}
                                    value={sensorRow.max_value}
                                    onChange={(e) =>
                                        handleChange(state.id, i, "max_value", e.target.value)
                                    }
                                    className="bg-slate-800 p-2 rounded w-24 text-white"
                                />
                            </div>
                        ))}
                    </div>
                ))}

                {/* Actions */}
                <div className="flex justify-end gap-2 mt-4">
                    <button onClick={onClose} className="px-4 py-2 bg-gray-600 rounded">
                        {t("common.cancel")}
                    </button>

                    <button
                        onClick={handleSubmit}
                        disabled={isLoading}
                        className="px-4 py-2 bg-emerald-600 rounded"
                    >
                        {isLoading ? t("common.saving") : t("common.save")}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default BaselineModal;