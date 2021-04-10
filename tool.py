import os
import matplotlib.pyplot as plt
def make_path(path):
    if not os.path.exists(path):
        os.makedirs(path)
    else:
        pass
    return path
def plot_smooth(save_fig=False, dcm_flag=True, png_name=None, dcm_name=None, num=None, **params):
    plot_num = len(params)
    if plot_num == 1:
        for key in params:
            plt.axis('off')
            plt.imshow(params[key])
    else:
        _, ax = plt.subplots(1, plot_num, figsize=(12, 4))
        for i, key in enumerate(params):
            ax[i].set_axis_off()
            ax[i].imshow(params[key])
            ax[i].set_title(key)
    if save_fig == False:
        plt.show()
    else:
        if dcm_flag == True:
            save_dcm_path = make_path(dcm_name.split('.')[0])
            plt.savefig(save_dcm_path + '/' + 'img_' + str(num) + '.png')
        else:
            save_png_path = make_path(png_name)
            plt.savefig(save_png_path + '/' + png_name + '.png')