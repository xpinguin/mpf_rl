function plot_nh()
    som_size = [5, 5];

    [model_errors, squared_dists_from_bmu] = ...
            meshgrid(0:0.01:1, 0:0.5:dot(som_size, som_size));
    
    plot3(model_errors, squared_dists_from_bmu, ...
        gauss_nh(model_errors, squared_dists_from_bmu), '-')
    
    xlabel('error');
    ylabel('distance');
    zlabel('NH');
    
function nh = gauss_nh(err, sq_dist_from_bmu)
    nh_const = 2.5;
    nh = exp(-sq_dist_from_bmu ./ ((nh_const .* err).^2));