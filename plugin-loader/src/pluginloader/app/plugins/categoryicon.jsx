define(
	['react', 'react-mdl'],
function(React, ReactMDL ) {
	class CategoryIcon extends React.Component {
		categoryIcon(category) {
			let categories = {
				'security': 'security',
				'weather': 'cloud',
				'cameras': 'camera_alt',
				'climate': 'ac_unit',
				'energy': 'power',
				'appliances': 'lightbulb_outline',
				'multimedia': 'music_note',
				'notifications': 'notifications',
				'upload': 'file_upload'
			}
			if (category in categories) {
				return categories[category]
			}
			return 'extension';
		}
		categoryName(category) {
			let categories = {
				'security': 'Security',
				'weather': 'Weather',
				'cameras': 'Cameras',
				'climate': 'Climate',
				'energy': 'Energy',
				'appliances': 'Lights & Appliances',
				'multimedia': 'Multimedia',
				'notifications': 'Notifications',
				'upload': 'Manual upload',
			}
			if (category in categories) {
				return categories[category]
			}
			return 'Other';
		}


		render() {
			return (
				<ReactMDL.Tooltip label={this.categoryName(this.props.category)} position="right">
					<ReactMDL.Icon name={this.categoryIcon(this.props.category)} style={{
						color: '#fff',
						backgroundColor: this.props.color,
						padding: '5px',
						borderRadius: '2px',
						marginRight: '7px',
						outline: 'none',
					}}/>
				</ReactMDL.Tooltip>
				)
		}
	}
	CategoryIcon.defaultProps = {
		color: '#757575',
	};
	return CategoryIcon;
});
