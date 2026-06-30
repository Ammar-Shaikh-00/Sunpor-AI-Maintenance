import React from 'react'
import { machineCriticalityColor } from '../../../assets/Data/ConstantData';
import { useTranslation } from "react-i18next";


const machineCard = ({ machine ,deleteMutation, setSelectedMachine,setIsEditing}) => {
    const { t } = useTranslation();    
  return (
    <div
        key={machine.id}
        className="bg-slate-900/70 border border-slate-700/40 rounded-2xl p-6 hover:border-emerald-500/40 transition-colors"
    >
        <div className="flex items-center justify-between">
            <div className="flex items-center gap-4"> 
                {/* <span className='text-xs'>{machine.status}</span> */}
                     
                <div> 
                    <h3 className="text-xl font-semibold text-slate-100">{machine.name}</h3>
                    <p className="text-sm text-slate-400">{machine.location}</p>
                    <span className={`text-xs px-2 py-0.5 rounded-full mt-1 inline-block ${machine.criticalColor}`} style={{backgroundColor: machineCriticalityColor[machine.criticality]}}
                    >
                        {machine.criticality}
                    </span>
                    
                </div>
            </div>
            <div className="flex items-center gap-3">
                <span className='bg-white/60 border-2 border-white rounded-lg p-1'>{machine.status} </span>
                <button
                    onClick={() => {
                        setSelectedMachine(machine);
                        setIsEditing(true);
                    }}
                    className="px-3 py-1.5 text-sm bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg transition-colors"
                >
                    {t("edit")}
                </button>
                {/* <button
                    onClick={() => {
                        const confirmed = window.confirm(
                            t("confirmDelete", { name: machine.name })
                        );
                        
                        if (confirmed) {
                            console.log("Deleting machine:", machine.id, machine.name);
                            deleteMutation.mutate(machine.id);
                        }
                    }}
                    disabled={deleteMutation.isPending}
                    className="px-3 py-1.5 text-sm bg-rose-600/20 hover:bg-rose-600/30 text-rose-200 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {deleteMutation.isPending ? t("deleting") : t("delete")}
                </button> */}
            </div>
        </div>
        <p className="text-sm text-slate-400">{t("createdAt")} {machine.created_at}</p>
        <p className="text-sm text-slate-400 mt-3">{t("description")} {machine.description}</p>
        
        
    </div>
  )
}

export default machineCard