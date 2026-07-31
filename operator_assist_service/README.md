# SUNPOR Operator Assist Service
#
# Lightweight automation service for operator suggestions.
# Runs as container `sunpor-operator-assist` on sunporNet (port 8010).
#
# Rules source:
#   Uses a local copy of AI_ML_Service/state/rules_config.yaml at
#   config/rules_config.yaml. Do not edit the AI_ML_Service original;
#   refresh the copy when ML rules change.
#
# Start:
#   docker compose up -d --build
#
# Backend calls POST http://sunpor-operator-assist:8010/analyze



# To start the program:
uvicorn app.main:app --host 0.0.0.0 --port 8010
