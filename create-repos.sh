#!/usr/bin/env bash
set -euo pipefail

TEMPLATE="iglesial/rag-kubeflow-starter"
OWNER="iglesial"
N="${1:-2}"
OFFSET="${2:-0}"

# First 151 French Pokémon names (no special chars)
POKEMONS=(
  bulbizarre herbizarre florizarre salameche reptincel dracaufeu
  carapuce carabaffe tortank chenipan chrysacier papilusion
  aspicot coconfort dardargnan roucool roucoups roucarnage
  rattata rattatac piafabec rapasdepic abo arbok pikachu raichu
  sabelette sablaireau nidoran-f nidorina nidoqueen nidoran-m
  nidorino nidoking melofee melodelfe caninos arcanin ptitard
  tetarte tartard abra kadabra alakazam machoc machopeur mackogneur
  chetiflor boustiflor empiflor tentacool tentacruel racaillou
  gravalanch grolem ponyta galopa ramoloss flagadoss magneti
  magneton canarticho doduo dodrio otaria lamantine tadmorv grotadmorv
  kokiyas crustabri fantominus spectrum ectoplasma onix soporifik
  hypnomade krabby krabboss voltorbe electrode noeunoeuf noadkoko
  osselait ossatueur kicklee tygnon excelangue smogo smogogo
  rhinocorne rhinoferos leveinard saquedeneu kangourex hypotrempe
  hypocean poissirene poissoroy stari staross m-mime insecateur
  lippoutou elektek magmar scarabrute tauros magicarpe leviator
  lokhlass metamorph evoli aquali voltali pyroli porygon amonita
  amonistar kabuto kabutops ptera ronflex artikodin electhor sulfura
  minidraco draco dracolosse mewtwo mew
)

if (( OFFSET + N > ${#POKEMONS[@]} )); then
  echo "OFFSET=$OFFSET + N=$N exceeds available Pokémon names (${#POKEMONS[@]})"
  exit 1
fi

for (( i=OFFSET; i<OFFSET+N; i++ )); do
  NAME="${POKEMONS[$i]}"
  REPO="${OWNER}/${NAME}"
  echo "Creating repo ${REPO} from template ${TEMPLATE}..."
  gh repo create "${REPO}" --template "${TEMPLATE}" --private
  echo "Created: https://github.com/${REPO}"
done

echo "Done! Created $N repos."
