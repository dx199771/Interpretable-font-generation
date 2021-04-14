import torch
import torch.nn as nn

class Generator(nn.Module):
    def __init__(self,channels,
                 img_size,
                 latent_dim,
                 code_dim):
        super(Generator, self).__init__()
        self.channels = channels
        self.img_size = img_size
        self.latent_dim = latent_dim
        self.code_dim = code_dim
        self.input_dim = self.latent_dim + self.code_dim
        self.init_size = self.img_size // 4  # Initial size before upsampling

        self.l1 = nn.Sequential(nn.Linear(self.input_dim, 128 * self.init_size ** 2))
        self.conv_blocks = nn.Sequential(
            nn.BatchNorm2d(128),
            nn.Upsample(scale_factor=2),
            nn.Conv2d(128, 128, 3, stride=1, padding=1),

            nn.BatchNorm2d(128, 0.8),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Upsample(scale_factor=2),
            nn.Conv2d(128, 64, 3, stride=1, padding=1),

            nn.BatchNorm2d(64, 0.8),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Conv2d(64, self.channels, 3, stride=1, padding=1),
            nn.Tanh(),
        )

    def forward(self, noise, code):
        gen_input = torch.cat((noise, code), -1)
        out = self.l1(gen_input)
        out = out.view(out.shape[0], 128, self.init_size, self.init_size)
        img = self.conv_blocks(out)

        return img


class Discriminator(nn.Module):
    def __init__(self,
                 channels,
                 img_size,
                 latent_dim,
                 code_dim):
        super(Discriminator, self).__init__()
        self.channels = channels
        self.img_size = img_size
        self.latent_dim = latent_dim
        self.code_dim = code_dim

        def discriminator_block(in_filters, out_filters, bn=True):
            """Returns layers of each discriminator block"""
            block = [nn.Conv2d(in_filters, out_filters, 3, 2, 1), nn.LeakyReLU(0.2, inplace=True), nn.Dropout2d(0.25)]
            if bn:
                block.append(nn.BatchNorm2d(out_filters, 0.8))
            return block

        self.conv_blocks = nn.Sequential(
            *discriminator_block(channels, 16, bn=False),
            *discriminator_block(16, 32),
            *discriminator_block(32, 64),
            *discriminator_block(64, 128),
        )

        # The height and width of downsampled image
        self.ds_size = self.img_size // 2 ** 4

        # Output layers
        self.adv_layer = nn.Sequential(nn.Linear(128 * self.ds_size ** 2, 1))
        self.latent_layer = nn.Sequential(nn.Linear(128 * self.ds_size ** 2, self.code_dim))

    def forward(self, img):

        out = self.conv_blocks(img)
        out = out.view(out.shape[0], -1)
        validity = self.adv_layer(out)
        latent_code = self.latent_layer(out)

        return validity, latent_code