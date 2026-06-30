import { useEffect, useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import safeApi from '../../../api/safeApi';
import { useErrorToast } from '../../subComponents/errorToast';
import { useTranslation } from "react-i18next";
import toast from 'react-hot-toast';

import BaselineModal from './baseModal';
import BaselineCard from './baslineCard';

const Baseline = () => {
    const { t } = useTranslation();
    const { showError, ErrorComponent } = useErrorToast();

    const [baselines, setBaselines] = useState([]);
    const [machineStates, setMachineStates] = useState([]);
    const [sensors, setSensors] = useState([]);

    const [loading, setLoading] = useState(true);

    const [showModal, setShowModal] = useState(false);
    const [isEditing, setIsEditing] = useState(false);
    const [selectedBaseline, setSelectedBaseline] = useState(null);

    // ✅ FETCH DATA
    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);

                const [b, ms, s] = await Promise.all([
                    safeApi.get("/baselines/baseline-maps"),
                    safeApi.get("/machine-state/default-machine-states"),
                    safeApi.get("/default-sensors"),
                ]);

                setBaselines(b.data || []);
                setMachineStates(ms.data || []);
                setSensors(s.data || []);

                // console.log(s.data);
                // console.log(sensors);
            } catch (err) {
                toast.error(t("messages.load_failed"));
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    // ✅ CREATE
    const createMutation = useMutation({
        mutationFn: (data) =>
            safeApi.post("/baselines/baseline-maps", data),


        onSuccess: (res) => {
            // console.log(res);
            setBaselines(prev => [...prev, res.data]);
            toast.success(t("messages.created"));
            setShowModal(false);
            setSelectedBaseline(null);
            setIsEditing(false);
        }
    });
    // ✅ UPDATE
    const updateMutation = useMutation({
        mutationFn: (data) =>
            safeApi.put(
                `/baselines/baseline-maps/${data.id}`,
                data
            ),

        onSuccess: (res) => {
            // console.log(res.data)
            setBaselines(prev =>
                prev.map(b =>
                    b.id === res.data?.id ? res.data : b
                )
            );
            toast.success(t("messages.updated"));
            setShowModal(false);
            setSelectedBaseline(null);
            setIsEditing(false);
        }
    });

    // ✅ DELETE
    const deleteMutation = useMutation({
        mutationFn: (id) =>
            safeApi.delete(`/baselines/baseline-maps/${id}`),

        onSuccess: (_, id) => {
            setBaselines(prev =>
                prev.filter(b => b.id !== id)
            );
        }
    });

    return (
        <div className="space-y-6">

            {/* HEADER */}
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-[#a551f4]">
                        {t("baseline.title")}
                    </h1>
                    <p className="text-slate-400">
                        {t("baseline.description")}
                    </p>
                </div>

                <button
                    onClick={() => {
                        setShowModal(true);
                        setIsEditing(false);
                    }}
                    className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 rounded text-white"
                >
                    + {t("baseline.create")}
                </button>
            </div>

            {/* LOADING */}
            {loading && (
                <div className="text-center text-slate-400 py-10">
                    {t("common.loading")}
                </div>
            )}

            {/* EMPTY */}
            {!loading && baselines.length === 0 && (
                <div className="text-center text-slate-400 py-10">
                    {t("baseline.no_data")}
                </div>
            )}

            {/* LIST */}
            {!loading && baselines.length > 0 && (
                <div className="grid gap-4">
                    {baselines.map((b) => (
                        <BaselineCard
                            key={b.id}
                            baseline={b}
                            deleteMutation={deleteMutation}
                            onEdit={(baseline) => {
                                setSelectedBaseline(baseline);
                                setIsEditing(true);
                                setShowModal(true);
                            }}
                        />
                    ))}
                </div>
            )}

            {/* MODAL */}
            <BaselineModal
                isOpen={showModal}
                onClose={() => {
                    setShowModal(false);
                    setIsEditing(false);
                    setSelectedBaseline(null);
                }}
                onSave={(data) => {
                            if (isEditing) {
                                const payload = {
                                    ...data,
                                    id: selectedBaseline.id   // ✅ safe add
                                };
                                console.log(payload)
                                updateMutation.mutate(payload);
                            } else {
                                createMutation.mutate(data);
                            }
                        }}
                machineStates={machineStates}
                sensors={sensors}
                isLoading={
                    createMutation.isPending || updateMutation.isPending
                }
                baseline={selectedBaseline}
                isEditing={isEditing}
            />

            {ErrorComponent}
        </div>
    );
};

export default Baseline;