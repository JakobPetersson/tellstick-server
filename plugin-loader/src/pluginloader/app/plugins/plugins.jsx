define(
	['react', 'react-mdl', 'telldus', 'plugins/actions', 'plugins/configureplugin', 'plugins/errormessage', 'plugins/keyslist', 'plugins/keyimport', 'plugins/pluginslist', 'plugins/upload'],
function(React, ReactMDL, Telldus, Actions, ConfigurePlugin, ErrorMessage, KeysList, KeyImport, PluginsList, Upload ) {
	var defaultState = {
		configure: null,
		importingKey: {
			keyid: null
		},
		keys: [],
		plugins: [],
		requireReboot: false,
		uploading: false,
		uploadErrorMsg: '',
	}

	function reducer(state = defaultState, action) {
		switch (action.type) {
			case 'CONFIGURATION_SAVED':
				return {...state, configure: null};
			case 'CONFIGURE_PLUGIN':
				return {...state, configure: action.plugin}
			case 'DISCARD_ERROR':
				return {...state, uploadErrorMsg: ''}
			case 'IMPORT_KEY':
				return {...state, importingKey: action.key}
			case 'KEY_ACCEPTED':
				return {...state, importingKey: {...defaultState.importingKey}}
			case 'KEY_DISCARDED':
				return {...state, importingKey: {...defaultState.importingKey}, uploading: false}
			case 'PLUGIN_UPLOADED':
				return {...state, uploading: false, uploadErrorMsg: ''}
			case 'RECEIVE_KEYS':
				return {...state, keys: action.keys};
			case 'RECEIVE_PLUGINS':
				return {...state, plugins: action.plugins};
			case 'UPLOAD_PLUGIN':
				return {...state, uploading: true, uploadErrorMsg: ''}
			case 'UPLOAD_PLUGIN_FAILED':
				return {...state, uploading: false, uploadErrorMsg: action.msg}
		}
		return state;
	}

	var store = Telldus.createStore(reducer)
	store.dispatch(Actions.fetchPlugins());
	store.dispatch(Actions.fetchKeys());

	class PluginsApp extends React.Component {
		render() {
			return (
				<div>
					<ReactMDL.Grid>
						<ReactMDL.Cell component={ReactMDL.Card} col={4} shadow={1}>
							<ReactMDL.CardTitle expand>Plugins</ReactMDL.CardTitle>
							<ReactMDL.CardText>
								<PluginsList store={store} />
							</ReactMDL.CardText>
						</ReactMDL.Cell>
						<ReactMDL.Cell component={ReactMDL.Card} col={3} shadow={1}>
							<ReactMDL.CardTitle expand>Upload</ReactMDL.CardTitle>
							<ReactMDL.CardText>
								Please select a plugin file and press the upload button to
								load a new plugin
							</ReactMDL.CardText>
							<ReactMDL.CardActions>
								<Upload store={store} />
							</ReactMDL.CardActions>
						</ReactMDL.Cell>
					</ReactMDL.Grid>
					{/*<ReactMDL.Grid>
						<ReactMDL.Cell component={ReactMDL.Card} col={7} shadow={1}>
							<ReactMDL.CardTitle expand>Trusted developers</ReactMDL.CardTitle>
							<ReactMDL.CardText>
								<KeysList store={store} />
							</ReactMDL.CardText>
						</ReactMDL.Cell>
					</ReactMDL.Grid>*/}
					<KeyImport store={store} />
					<ConfigurePlugin store={store} />
					<ErrorMessage store={store} />
				</div>
			)
		}
	};

	return PluginsApp;
});
