
import { useEffect, useState } from 'react';
import MachineCard from './machineCard';
import { useMutation } from '@tanstack/react-query';
import { MachineModal } from './machineModal';
import safeApi from '../../../api/safeApi';
import { useErrorToast } from '../../subComponents/errorToast';
import { useTranslation } from "react-i18next";
import toast from 'react-hot-toast';
  


const machine = () => {
    const { t } = useTranslation();
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [isEditing, setIsEditing] = useState(false);
    const [selectedMachine, setSelectedMachine] = useState(null);
    const { showError, ErrorComponent } = useErrorToast();

    const [machines, setMachines] = useState([]);
    const [loading, setLoading] = useState(true);

    // ✅ FETCH MACHINES
    useEffect(() => {
        const fetchMachines = async () => {
        try {
            setLoading(true);
            const response = await safeApi.get("/machines");
            setMachines(response.data || []);
            console.log(machines);
        } catch (error) {
            console.error("Error fetching machines:", error);
        } finally {
            setLoading(false);
        }
        };

        fetchMachines();
    }, []);
    

    const deleteMutation = useMutation({
        mutationFn: (id) => {
            const machineId = typeof id === "string" ? id : String(id);
            return safeApi.delete(`/machines/${machineId}`);
        },

        onSuccess: (_, id) => {
            // ✅ manually remove from state
            setMachines((prev) => prev.filter((m) => m.id !== id));

            showError("✅ Machine deleted successfully!");
        },

        onError: (error) => {
            const errorMessage =
                error.response?.data?.detail ||
                error.message ||
                "Unknown error";

            console.error("Delete machine error:", error);
            showError(`❌ Failed to delete machine: ${errorMessage}`);
        },
    });


    const updateMutation = useMutation({
        mutationFn: ({ id, data }) =>
            safeApi.put(`/machines/${id}`, data),

        onSuccess: (res, variables) => {

            if (res?.fallback) {
                showError(res?.error || "Failed to update machine");
                return;
            }

            setMachines((prev) =>
                prev.map((m) =>
                    m.id === variables.id
                        ? { ...m, ...variables.data }
                        : m
                )
            );

            setIsEditing(false);
            setSelectedMachine(null);

            toast.success("Machine updated successfully");
        },

        onError: (error) => {
            showError(
                `❌ Failed to update machine: ${
                    error.response?.data?.detail || error.message
                }`
            );
        },
    });

    const createMutation = useMutation({
        mutationFn: (data) => safeApi.post("/machines", data),

        onSuccess: (res) => {
            // queryClient.invalidateQueries({ queryKey: ["machines"] });
            setMachines((prev) => [...prev, res.data]);
            setShowCreateModal(false);
            showError("✅ Machine created successfully!");
        },

        onError: (error) => {
            showError(
                `❌ Failed to create machine: ${
                    error.response?.data?.detail || error.message
                }`
            );
        },
    });

  return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-[#a551f4]">{t("machines")}</h1>
                    <p className="text-slate-400 mt-1">{t("manageMachines")}</p>
                </div>
                <button
                    onClick={() => setShowCreateModal(true)}
                    className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-medium transition-colors"
                >
                    + {t("addMachine")}
                </button>
            </div>

            {/* ✅ LOADING STATE */}
            {loading && (
                <div className="text-center text-slate-400 py-10">
                {t("loadingMachines")}
                </div>
            )}

            {/* ✅ EMPTY STATE */}
            {!loading && machines.length === 0 && (
                <div className="text-center text-slate-400 py-10">
                {t("noMachines")}
                </div>
            )}

            {/* ✅ LIST */}
            {!loading && machines.length > 0 && (
                <div className="grid gap-4">
                {machines.map((machine) => (
                    <MachineCard
                    key={machine.id}
                    machine={machine}
                    deleteMutation={deleteMutation}
                    setSelectedMachine={setSelectedMachine}
                    setIsEditing={setIsEditing}
                    />
                ))}
                </div>
            )}

            <MachineModal
                isOpen={showCreateModal || isEditing}
                onClose={() => {
                    setShowCreateModal(false);
                    setIsEditing(false);
                    setSelectedMachine(null);
                }}
                onSave={(data) => {
                    if (isEditing && selectedMachine) {
                        updateMutation.mutate({ id: selectedMachine.id, data });
                    } else {
                        createMutation.mutate(data);
                    }
                }}
                machine={selectedMachine}
                isEditing={isEditing}
                isLoading={createMutation.isPending || updateMutation.isPending}
            />

            {ErrorComponent}
        </div>
  )
}

export default machine