from bokeh.models import Select

class GlobalSettings:
    def __init__(self, data_loader):
        self.data_loader = data_loader

        # Dynamically populate champion options
        self.global_settings = {
            "champion": Select(
                title="Select Champion:",
                options=self.data_loader.get_unique_champions(),
                value=self.data_loader.get_unique_champions()[0] if self.data_loader.get_unique_champions() else None,
            ),
            "role": Select(
                title="Select Role:",
                options=self.data_loader.get_roles(),
                value="ANY",
            ),
        }

    def layout(self):
        return [self.global_settings[key] for key in self.global_settings]
