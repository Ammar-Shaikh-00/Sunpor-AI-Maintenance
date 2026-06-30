import React from "react";
import { Info } from "lucide-react";

const SensorCard=({sensor, setSelectedSensor, setIsEditing, deleteMutation})=>{

const featureMessage=()=>{

alert(
`🚧 Feature under development

Update/Delete APIs are not available yet.
These actions will be enabled when backend support arrives.`
)

}

return(

    <div className="
    bg-slate-900
    border border-slate-700
    rounded-2xl
    p-5">

        <div className="
        flex justify-between items-center">

        <div>

        <h2 className="
        text-xl
        font-semibold
        text-white">

        {sensor.name}

        </h2>

        <p className="
        text-slate-400
        mt-1">

        Map Value:
        <span className="text-emerald-400 ml-2">
        {sensor.map_val || "-"}
        </span>

        </p>

        </div>


    <div className="flex gap-2">

    <button
        onClick={()=>{
        setSelectedSensor(sensor)
        setIsEditing(true)
        }}
        className="px-4 py-2 bg-slate-800 rounded"
    >
        Edit
    </button>


    <button
        onClick={()=>{

        if(
        window.confirm(
        `Delete ${sensor.name}?`
        )
        ){
        deleteMutation.mutate(sensor.id)
        }

        }}
        className="px-4 py-2 bg-red-600 rounded"
    >
        Delete
    </button>

    </div>

    </div>


    {/* <div className="
    mt-4
    flex items-center
    gap-2
    text-sm
    text-amber-400">

    <Info size={16}/>

    Update/Delete API not available

    </div> */}

    </div>

)

}

export default SensorCard