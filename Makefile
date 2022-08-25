# ----------------------------------------------------------
# Building and running the app
# ----------------------------------------------------------

# Default: Build and deploy
deploy:
	swagger-cli bundle -o api/api.yaml --dereference --t yaml  api/apiSkeleton.yaml
	swagger-cli validate api/api.yaml
	cfn-include --yaml  cloudFormation/templateSkeleton.yaml > template.yaml
	sam build -t template.yaml
	sam deploy --stack-name $$STACKNAME --s3-bucket $$BUCKETNAME --capabilities CAPABILITY_IAM

# Compile openAPI components into a single file
buildOpenApi:
	swagger-cli bundle -o api/api.yaml --dereference --t yaml  api/apiSkeleton.yaml
	swagger-cli validate api/api.yaml

# Compile cloudformation resources into a single file
buildTemplate:
	cfn-include --yaml  cloudFormation/templateSkeleton.yaml > template.yaml

# Package but not deploy (Example for a CodeBuild/buildspec.yaml build stage)
packageOnly:
	swagger-cli bundle -o api/api.yaml --dereference --t yaml  api/apiSkeleton.yaml
	cfn-include --yaml  cloudFormation/templateSkeleton.yaml > template.yaml
	sam build --parallel && sam package --template-file .aws-sam/build/template.yaml --s3-bucket $$BUCKETNAME  --output-template-file packaged.yaml --no-progressbar
	echo "Output Build Asset: packaged.yaml"

# Activate python environment
activate:
	source .venv/bin/activate

# ----------------------------------------------------------
# Generating the OpenApi documentation
# ----------------------------------------------------------

generateApiDoc:
	make buildOpenApi
	openapi-generator generate -i api/api.yaml -g html2 -o ./apidocs

# ----------------------------------------------------------
# Testing the app
# ----------------------------------------------------------

# Run all tests
pyTest:
	python -m unittest discover

# Run tests with coverage
coverage:
	coverage run -m unittest discover
	coverage report -m --omit ".venv/*","tests/*"

# Run tests with coverage and see results in browser (must have default browser setup)
coverageHtml:
	coverage run -m unittest discover
	coverage html --omit ".venv/*","tests/*"
	open htmlcov/index.html

testAll:
	coverage run -m unittest discover
	coverage report -m --omit ".venv/*","tests/*"
	bandit -r  . -x ".venv,.aws-sam,venv" -s "B101" -f txt
	swagger-cli validate api/api.yaml
	cfn_nag_scan --input-path template.yaml --blacklist-path cfn_nag_config.yaml

# ----------------------------------------------------------
# Installing Utilities and Test Suites
# ----------------------------------------------------------
setup:
	python3 -m venv .venv
	pip install --upgrade pip
	pip install cfn-lint
	pip install -r tests/requirements.txt
	pip install coverage
	pip install bandit
	npm -v
	npm update -g
	npm install -g @apidevtools/swagger-cli
	npm install -g @openapitools/openapi-generator-cli
	npm install -g cfn-include
	gem install cfn-nag

# ----------------------------------------------------------
# List available commands
# ----------------------------------------------------------
list:
	@grep '^[^#[:space:]].*:' Makefile